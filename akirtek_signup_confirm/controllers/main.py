import logging

from odoo import _
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.web.controllers.home import Home
from odoo.exceptions import UserError
from odoo.http import request, route

_logger = logging.getLogger(__name__)


class Main(Home):
    def _get_input_sinugp_email(self):
        return ["name", "email"]

    def _send_welcome_email(self, partner_id):
        template = request.env.ref(
            "akirtek_signup_confirm.mail_template_data_portal_grant_access"
        )
        if not template:
            raise UserError(
                _(
                    'The template "Portal: new user" not found for sending email to the portal user.'
                )
            )

        partner = partner_id.sudo()

        portal_url = partner.with_context(
            signup_force_type_in_url="", lang=partner.lang
        )._get_signup_url_for_action()[partner.id]
        partner.signup_prepare()

        template.with_context(
            dbname=request._cr.dbname, portal_url=portal_url, lang=partner.lang
        ).sudo().send_mail(partner.user_ids[0].id, force_send=True)

        return True

    def _prepare_partner_values(self, qcontext):
        values = {key: qcontext.get(key) for key in ("email", "name")}
        if not values:
            raise UserError(_("The form was not properly filled in."))
        supported_lang_codes = [
            code for code, _ in request.env["res.lang"].get_installed()
        ]
        lang = request.context.get("lang", "")
        if lang in supported_lang_codes:
            values["lang"] = lang
        return values

    def _create_user(self, email, partner_id):
        return (
            request.env["res.users"]
            .with_context(no_reset_password=True)
            .sudo()
            ._create_user_from_template(
                {
                    "email": email,
                    "login": email,
                    "partner_id": partner_id.id,
                    "company_id": request.env.company.id,
                    "company_ids": [(6, 0, request.env.company.ids)],
                }
            )
        )

    def _user_create_message(self):
        return _(
            "Your email has been registered successfully. Please check your email for the confirmation link."
        )

    @route(
        "/signup/email",
        type="http",
        auth="public",
        website=True,
        sitemap=False,
        methods=["GET", "POST"],
    )
    def web_auth_signup_email(self, *args, **kw):
        signup_email_template = "akirtek_signup_confirm.signup_email"
        qcontext = {
            k: v
            for (k, v) in request.params.items()
            if k in self._get_input_sinugp_email()
        }
        qcontext.update(self.get_auth_signup_config())
        user_actived = False
        if request.httprequest.method == "POST":
            user_actived = False
            partner_obj = request.env["res.partner"].sudo()
            partner_id = partner_obj.search(
                [("email", "=", qcontext.get("email"))], limit=1
            ).sudo()
            user_id = False
            if partner_id:
                user_id = (
                    request.env["res.users"]
                    .sudo()
                    .search(
                        [
                            ("partner_id", "=", partner_id.id),
                            ("active", "in", [True, False]),
                        ],
                        limit=1,
                    )
                )
            if partner_id and user_id and user_id.active:
                qcontext["error"] = _(
                    "Another user is already registered using this email address."
                )
            elif partner_id and user_id and not user_id.active:
                user_id.active = True
                user_actived = True
            elif partner_id and not user_id:
                self._create_user(qcontext.get("email"), partner_id)
                user_actived = True
            else:
                try:
                    values = self._prepare_partner_values(qcontext)
                    partner_id = partner_obj.create(values)
                    self._create_user(values["email"], partner_id)
                except Exception as e:
                    qcontext["error"] = (
                        "Could not create a new account." + "\n" + str(e)
                    )
                    _logger.warning(e)
                else:
                    _logger.info(
                        "Email registered successfully: %s", qcontext.get("login")
                    )
                    user_sudo = partner_id.user_id.sudo()
                    user_sudo.partner_id.signup_prepare()
                    user_actived = True

        if user_actived:
            self._send_welcome_email(partner_id)
            qcontext["message"] = self._user_create_message()
        response = request.render(signup_email_template, qcontext)
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Content-Security-Policy"] = "frame-ancestors 'self'"
        return response


class AuthSignupHome(AuthSignupHome):
    @route("/web/signup", type="http", auth="public", website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()
        if not qcontext.get("token"):
            return request.redirect("/signup/email", 303)
        return super().web_auth_signup(*args, **kw)

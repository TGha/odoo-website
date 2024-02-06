# License GPL-3.0 or later (https://www.gnu.org/licenses/gpl-3.0).
{
    "name": "Website Signup Confirm",
    "version": "17.0.1.0.0",
    "author": "A. Tsiorimampionina, RAVALISON, Akirtek",
    "license": "GPL-3",
    "application": False,
    "installable": True,
    "category": "Website",
    "summary": "Added confirmation when registering in Odoo",
    "depends": ["website"],
    "data": [
        "data/mail_template_data.xml",
        "templates/template.xml",
        "views/res_partner.xml",
    ],
}

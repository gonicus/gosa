# -*- encoding: utf-8 -*-
# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import gettext
import pycountry
from gosa.common.components import Command
from gosa.common.components import Plugin
from gosa.common.utils import N_
from pkg_resources import resource_filename #@UnresolvedImport


class Locales(Plugin):
    _target_ = 'misc'

    __locales_map = {
          "af_ZA": N_("Afrikaans (South Africa)"),
          "sq_AL.UTF-8": N_("Albanian"),
          "ar_DZ.UTF-8": N_("Arabic (Algeria)"),
          "ar_BH.UTF-8": N_("Arabic (Bahrain)"),
          "ar_EG.UTF-8": N_("Arabic (Egypt)"),
          "ar_IN.UTF-8": N_("Arabic (India)"),
          "ar_IQ.UTF-8": N_("Arabic (Iraq)"),
          "ar_JO.UTF-8": N_("Arabic (Jordan)"),
          "ar_KW.UTF-8": N_("Arabic (Kuwait)"),
          "ar_LB.UTF-8": N_("Arabic (Lebanon)"),
          "ar_LY.UTF-8": N_("Arabic (Libyan Arab Jamahiriya)"),
          "ar_MA.UTF-8": N_("Arabic (Morocco)"),
          "ar_OM.UTF-8": N_("Arabic (Oman)"),
          "ar_QA.UTF-8": N_("Arabic (Qatar)"),
          "ar_SA.UTF-8": N_("Arabic (Saudi Arabia)"),
          "ar_SD.UTF-8": N_("Arabic (Sudan)"),
          "ar_SY.UTF-8": N_("Arabic (Syrian Arab Republic)"),
          "ar_TN.UTF-8": N_("Arabic (Tunisia)"),
          "ar_AE.UTF-8": N_("Arabic (United Arab Emirates)"),
          "ar_YE.UTF-8": N_("Arabic (Yemen)"),
          "as_IN.UTF-8": N_("Assamese (India)"),
          "ast_ES.UTF-8": N_("Asturian (Spain)"),
          "eu_ES.UTF-8": N_("Basque (Spain)"),
          "be_BY.UTF-8": N_("Belarusian"),
          "bn_BD.UTF-8": N_("Bengali (BD)"),
          "bn_IN.UTF-8": N_("Bengali (India)"),
          "bs_BA": N_("Bosnian (Bosnia and Herzegowina)"),
          "br_FR": N_("Breton (France)"),
          "bg_BG.UTF-8": N_("Bulgarian - Български"),
          "ca_ES.UTF-8": N_("Catalan (Spain)"),
          "zh_HK.UTF-8": N_("Chinese (Hong Kong)"),
          "zh_CN.UTF-8": N_("Chinese (P.R. of China) - 中文(简体)"),
          "zh_TW.UTF-8": N_("Chinese (Taiwan) - 正體中文"),
          "kw_GB.UTF-8": N_("Cornish (Britain)"),
          "hr_HR.UTF-8": N_("Croatian"),
          "cs_CZ.UTF-8": N_("Czech - Česká republika"),
          "da_DK.UTF-8": N_("Danish - Dansk"),
          "nl_BE.UTF-8": N_("Dutch (Belgium)"),
          "nl_NL.UTF-8": N_("Dutch (Netherlands)"),
          "en_AU.UTF-8": N_("English (Australia)"),
          "en_BW.UTF-8": N_("English (Botswana)"),
          "en_CA.UTF-8": N_("English (Canada)"),
          "en_DK.UTF-8": N_("English (Denmark)"),
          "en_GB.UTF-8": N_("English (Great Britain)"),
          "en_HK.UTF-8": N_("English (Hong Kong)"),
          "en_IN.UTF-8": N_("English (India)"),
          "en_IE.UTF-8": N_("English (Ireland)"),
          "en_NZ.UTF-8": N_("English (New Zealand)"),
          "en_PH.UTF-8": N_("English (Philippines)"),
          "en_SG.UTF-8": N_("English (Singapore)"),
          "en_ZA.UTF-8": N_("English (South Africa)"),
          "en_US.UTF-8": N_("English (USA)"),
          "en_ZW.UTF-8": N_("English (Zimbabwe)"),
          "et_EE.UTF-8": N_("Estonian"),
          "fo_FO.UTF-8": N_("Faroese (Faroe Islands)"),
          "fi_FI.UTF-8": N_("Finnish"),
          "fr_BE.UTF-8": N_("French (Belgium)"),
          "fr_CA.UTF-8": N_("French (Canada)"),
          "fr_FR.UTF-8": N_("French (France) - Français"),
          "fr_LU.UTF-8": N_("French (Luxemburg)"),
          "fr_CH.UTF-8": N_("French (Switzerland)"),
          "gl_ES.UTF-8": N_("Galician (Spain)"),
          "de_AT.UTF-8": N_("German (Austria)"),
          "de_BE.UTF-8": N_("German (Belgium)"),
          "de_DE.UTF-8": N_("German (Germany) - Deutsch"),
          "de_LU.UTF-8": N_("German (Luxemburg)"),
          "de_CH.UTF-8": N_("German (Switzerland)"),
          "el_GR.UTF-8": N_("Greek"),
          "kl_GL.UTF-8": N_("Greenlandic (Greenland)"),
          "gu_IN.UTF-8": N_("Gujarati (India)"),
          "he_IL.UTF-8": N_("Hebrew (Israel)"),
          "hi_IN.UTF-8": N_("Hindi (India)"),
          "hu_HU.UTF-8": N_("Hungarian"),
          "is_IS.UTF-8": N_("Icelandic - Íslenska"),
          "id_ID.UTF-8": N_("Indonesian"),
          "ga_IE.UTF-8": N_("Irish"),
          "it_IT.UTF-8": N_("Italian (Italy) Italiano"),
          "it_CH.UTF-8": N_("Italian (Switzerland)"),
          "ja_JP.UTF-8": N_("Japanese - 日本語"),
          "kn_IN.UTF-8": N_("Kannada (India)"),
          "ko_KR.UTF-8": N_("Korean (Republic of Korea) - 한국어"),
          "lo_LA.UTF-8": N_("Lao (Laos)"),
          "lv_LV.UTF-8": N_("Latvian (Latvia)"),
          "lt_LT.UTF-8": N_("Lithuanian"),
          "mk_MK.UTF-8": N_("Macedonian"),
          "mai_IN.UTF-8": N_("Maithili (India)"),
          "ml_IN.UTF-8": N_("Malayalam (India)"),
          "ms_MY.UTF-8": N_("Malay (Malaysia)"),
          "mt_MT.UTF-8": N_("Maltese (malta)"),
          "gv_GB.UTF-8": N_("Manx Gaelic (Britain)"),
          "mr_IN.UTF-8": N_("Marathi (India)"),
          "se_NO": N_("Northern Saami (Norway)"),
          "ne_NP.UTF-8": N_("Nepali (Nepal)"),
          "nb_NO.UTF-8": N_("Norwegian - Norsk"),
          "nn_NO.UTF-8": N_("Norwegian, Nynorsk (Norway) - Norsk"),
          "oc_FR": N_("Occitan (France)"),
          "or_IN.UTF-8": N_("Oriya (India)"),
          "fa_IR.UTF-8": N_("Persian (Iran)"),
          "pl_PL.UTF-8": N_("Polish"),
          "pt_BR.UTF-8": N_("Portuguese (Brasil)"),
          "pt_PT.UTF-8": N_("Portuguese (Portugal) - Português"),
          "pa_IN.UTF-8": N_("Punjabi (India)"),
          "ro_RO.UTF-8": N_("Romanian"),
          "ru_RU.UTF-8": N_("Russian - Русский"),
          "ru_UA.UTF-8": N_("Russian (Ukraine)"),
          "sr_RS.UTF-8": N_("Serbian"),
          "sr_RS.UTF-8@latin": N_("Serbian (Latin)"),
          "si_LK.UTF-8": N_("Sinhala"),
          "sk_SK.UTF-8": N_("Slovak"),
          "sl_SI.UTF-8": N_("Slovenian (Slovenia) - slovenščina"),
          "es_AR.UTF-8": N_("Spanish (Argentina)"),
          "es_BO.UTF-8": N_("Spanish (Bolivia)"),
          "es_CL.UTF-8": N_("Spanish (Chile)"),
          "es_CO.UTF-8": N_("Spanish (Colombia)"),
          "es_CR.UTF-8": N_("Spanish (Costa Rica)"),
          "es_DO.UTF-8": N_("Spanish (Dominican Republic)"),
          "es_SV.UTF-8": N_("Spanish (El Salvador)"),
          "es_EC.UTF-8": N_("Spanish (Equador)"),
          "es_GT.UTF-8": N_("Spanish (Guatemala)"),
          "es_HN.UTF-8": N_("Spanish (Honduras)"),
          "es_MX.UTF-8": N_("Spanish (Mexico)"),
          "es_NI.UTF-8": N_("Spanish (Nicaragua)"),
          "es_PA.UTF-8": N_("Spanish (Panama)"),
          "es_PY.UTF-8": N_("Spanish (Paraguay)"),
          "es_PE.UTF-8": N_("Spanish (Peru)"),
          "es_PR.UTF-8": N_("Spanish (Puerto Rico)"),
          "es_ES.UTF-8": N_("Spanish (Spain) - Español"),
          "es_US.UTF-8": N_("Spanish (USA)"),
          "es_UY.UTF-8": N_("Spanish (Uruguay)"),
          "es_VE.UTF-8": N_("Spanish (Venezuela)"),
          "sv_FI.UTF-8": N_("Swedish (Finland)"),
          "sv_SE.UTF-8": N_("Swedish (Sweden) - Svenska"),
          "tl_PH": N_("Tagalog (Philippines)"),
          "ta_IN.UTF-8": N_("Tamil (India)"),
          "te_IN.UTF-8": N_("Telugu (India)"),
          "th_TH.UTF-8": N_("Thai"),
          "tr_TR.UTF-8": N_("Turkish"),
          "uk_UA.UTF-8": N_("Ukrainian"),
          "ur_PK": N_("Urdu (Pakistan)"),
          "uz_UZ": N_("Uzbek (Uzbekistan)"),
          "wa_BE@euro": N_("Walloon (Belgium)"),
          "cy_GB.UTF-8": N_("Welsh (Great Britain)"),
          "xh_ZA.UTF-8": N_("Xhosa (South Africa)"),
          "zu_ZA.UTF-8": N_("Zulu (South Africa)")
     }
    __languages = None

    def __init__(self):
        self.__locales = {}

        for lang, description in self.__locales_map.items():
            _lang = lang.split("_")[0]
            self.__locales[lang] = {'value': "%s" % description, 'icon': 'flags/%s.png' % _lang}

    @Command(__help__=N_("Return list of languages"))
    def getLanguageList(self, locale=None):
        """
        Deliver a dictionary of language code/display name
        mapping for all supported languages.
           ``Return:`` Dictionary
        """
        if not locale:
            return self.__locales

        # Translate to the requested language
        _locales = {}
        t = gettext.translation('messages', resource_filename('gosa.backend', "locale"),
                                fallback=True, languages=[locale])

        for lang, info in self.__locales.items():
            _locales[lang] = info
            _locales[lang]['value'] = t.gettext(_locales[lang]['value'])

        return _locales

    @Command(__help__=N_("Return list of countries"))
    def getCountryList(self):

        if self.__languages is None:
            self.__languages = {}
            for country in pycountry.countries:
                self.__languages[country.alpha_2.lower()] = country.name

        return self.__languages

    def get_locales_map(self):
        return self.__locales_map

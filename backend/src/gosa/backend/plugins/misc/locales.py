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
from gosa.common.components import Command
from gosa.common.components import Plugin
from gosa.common.utils import N_
from pkg_resources import resource_filename #@UnresolvedImport


class Locales(Plugin):
    _target_ = 'misc'

    __locales_map = {
         "af_ZA": N_(u"Afrikaans (South Africa)"),
         "sq_AL.UTF-8": N_(u"Albanian"),
         "ar_DZ.UTF-8": N_(u"Arabic (Algeria)"),
         "ar_BH.UTF-8": N_(u"Arabic (Bahrain)"),
         "ar_EG.UTF-8": N_(u"Arabic (Egypt)"),
         "ar_IN.UTF-8": N_(u"Arabic (India)"),
         "ar_IQ.UTF-8": N_(u"Arabic (Iraq)"),
         "ar_JO.UTF-8": N_(u"Arabic (Jordan)"),
         "ar_KW.UTF-8": N_(u"Arabic (Kuwait)"),
         "ar_LB.UTF-8": N_(u"Arabic (Lebanon)"),
         "ar_LY.UTF-8": N_(u"Arabic (Libyan Arab Jamahiriya)"),
         "ar_MA.UTF-8": N_(u"Arabic (Morocco)"),
         "ar_OM.UTF-8": N_(u"Arabic (Oman)"),
         "ar_QA.UTF-8": N_(u"Arabic (Qatar)"),
         "ar_SA.UTF-8": N_(u"Arabic (Saudi Arabia)"),
         "ar_SD.UTF-8": N_(u"Arabic (Sudan)"),
         "ar_SY.UTF-8": N_(u"Arabic (Syrian Arab Republic)"),
         "ar_TN.UTF-8": N_(u"Arabic (Tunisia)"),
         "ar_AE.UTF-8": N_(u"Arabic (United Arab Emirates)"),
         "ar_YE.UTF-8": N_(u"Arabic (Yemen)"),
         "as_IN.UTF-8": N_(u"Assamese (India)"),
         "ast_ES.UTF-8": N_(u"Asturian (Spain)"),
         "eu_ES.UTF-8": N_(u"Basque (Spain)"),
         "be_BY.UTF-8": N_(u"Belarusian"),
         "bn_BD.UTF-8": N_(u"Bengali (BD)"),
         "bn_IN.UTF-8": N_(u"Bengali (India)"),
         "bs_BA": N_(u"Bosnian (Bosnia and Herzegowina)"),
         "br_FR": N_(u"Breton (France)"),
         "bg_BG.UTF-8": N_(u"Bulgarian - Български"),
         "ca_ES.UTF-8": N_(u"Catalan (Spain)"),
         "zh_HK.UTF-8": N_(u"Chinese (Hong Kong)"),
         "zh_CN.UTF-8": N_(u"Chinese (P.R. of China) - 中文(简体)"),
         "zh_TW.UTF-8": N_(u"Chinese (Taiwan) - 正體中文"),
         "kw_GB.UTF-8": N_(u"Cornish (Britain)"),
         "hr_HR.UTF-8": N_(u"Croatian"),
         "cs_CZ.UTF-8": N_(u"Czech - Česká republika"),
         "da_DK.UTF-8": N_(u"Danish - Dansk"),
         "nl_BE.UTF-8": N_(u"Dutch (Belgium)"),
         "nl_NL.UTF-8": N_(u"Dutch (Netherlands)"),
         "en_AU.UTF-8": N_(u"English (Australia)"),
         "en_BW.UTF-8": N_(u"English (Botswana)"),
         "en_CA.UTF-8": N_(u"English (Canada)"),
         "en_DK.UTF-8": N_(u"English (Denmark)"),
         "en_GB.UTF-8": N_(u"English (Great Britain)"),
         "en_HK.UTF-8": N_(u"English (Hong Kong)"),
         "en_IN.UTF-8": N_(u"English (India)"),
         "en_IE.UTF-8": N_(u"English (Ireland)"),
         "en_NZ.UTF-8": N_(u"English (New Zealand)"),
         "en_PH.UTF-8": N_(u"English (Philippines)"),
         "en_SG.UTF-8": N_(u"English (Singapore)"),
         "en_ZA.UTF-8": N_(u"English (South Africa)"),
         "en_US.UTF-8": N_(u"English (USA)"),
         "en_ZW.UTF-8": N_(u"English (Zimbabwe)"),
         "et_EE.UTF-8": N_(u"Estonian"),
         "fo_FO.UTF-8": N_(u"Faroese (Faroe Islands)"),
         "fi_FI.UTF-8": N_(u"Finnish"),
         "fr_BE.UTF-8": N_(u"French (Belgium)"),
         "fr_CA.UTF-8": N_(u"French (Canada)"),
         "fr_FR.UTF-8": N_(u"French (France) - Français"),
         "fr_LU.UTF-8": N_(u"French (Luxemburg)"),
         "fr_CH.UTF-8": N_(u"French (Switzerland)"),
         "gl_ES.UTF-8": N_(u"Galician (Spain)"),
         "de_AT.UTF-8": N_(u"German (Austria)"),
         "de_BE.UTF-8": N_(u"German (Belgium)"),
         "de_DE.UTF-8": N_(u"German (Germany) - Deutsch"),
         "de_LU.UTF-8": N_(u"German (Luxemburg)"),
         "de_CH.UTF-8": N_(u"German (Switzerland)"),
         "el_GR.UTF-8": N_(u"Greek"),
         "kl_GL.UTF-8": N_(u"Greenlandic (Greenland)"),
         "gu_IN.UTF-8": N_(u"Gujarati (India)"),
         "he_IL.UTF-8": N_(u"Hebrew (Israel)"),
         "hi_IN.UTF-8": N_(u"Hindi (India)"),
         "hu_HU.UTF-8": N_(u"Hungarian"),
         "is_IS.UTF-8": N_(u"Icelandic - Íslenska"),
         "id_ID.UTF-8": N_(u"Indonesian"),
         "ga_IE.UTF-8": N_(u"Irish"),
         "it_IT.UTF-8": N_(u"Italian (Italy) Italiano"),
         "it_CH.UTF-8": N_(u"Italian (Switzerland)"),
         "ja_JP.UTF-8": N_(u"Japanese - 日本語"),
         "kn_IN.UTF-8": N_(u"Kannada (India)"),
         "ko_KR.UTF-8": N_(u"Korean (Republic of Korea) - 한국어"),
         "lo_LA.UTF-8": N_(u"Lao (Laos)"),
         "lv_LV.UTF-8": N_(u"Latvian (Latvia)"),
         "lt_LT.UTF-8": N_(u"Lithuanian"),
         "mk_MK.UTF-8": N_(u"Macedonian"),
         "mai_IN.UTF-8": N_(u"Maithili (India)"),
         "ml_IN.UTF-8": N_(u"Malayalam (India)"),
         "ms_MY.UTF-8": N_(u"Malay (Malaysia)"),
         "mt_MT.UTF-8": N_(u"Maltese (malta)"),
         "gv_GB.UTF-8": N_(u"Manx Gaelic (Britain)"),
         "mr_IN.UTF-8": N_(u"Marathi (India)"),
         "se_NO": N_(u"Northern Saami (Norway)"),
         "ne_NP.UTF-8": N_(u"Nepali (Nepal)"),
         "nb_NO.UTF-8": N_(u"Norwegian - Norsk"),
         "nn_NO.UTF-8": N_(u"Norwegian, Nynorsk (Norway) - Norsk"),
         "oc_FR": N_(u"Occitan (France)"),
         "or_IN.UTF-8": N_(u"Oriya (India)"),
         "fa_IR.UTF-8": N_(u"Persian (Iran)"),
         "pl_PL.UTF-8": N_(u"Polish"),
         "pt_BR.UTF-8": N_(u"Portuguese (Brasil)"),
         "pt_PT.UTF-8": N_(u"Portuguese (Portugal) - Português"),
         "pa_IN.UTF-8": N_(u"Punjabi (India)"),
         "ro_RO.UTF-8": N_(u"Romanian"),
         "ru_RU.UTF-8": N_(u"Russian - Русский"),
         "ru_UA.UTF-8": N_(u"Russian (Ukraine)"),
         "sr_RS.UTF-8": N_(u"Serbian"),
         "sr_RS.UTF-8@latin": N_(u"Serbian (Latin)"),
         "si_LK.UTF-8": N_(u"Sinhala"),
         "sk_SK.UTF-8": N_(u"Slovak"),
         "sl_SI.UTF-8": N_(u"Slovenian (Slovenia) - slovenščina"),
         "es_AR.UTF-8": N_(u"Spanish (Argentina)"),
         "es_BO.UTF-8": N_(u"Spanish (Bolivia)"),
         "es_CL.UTF-8": N_(u"Spanish (Chile)"),
         "es_CO.UTF-8": N_(u"Spanish (Colombia)"),
         "es_CR.UTF-8": N_(u"Spanish (Costa Rica)"),
         "es_DO.UTF-8": N_(u"Spanish (Dominican Republic)"),
         "es_SV.UTF-8": N_(u"Spanish (El Salvador)"),
         "es_EC.UTF-8": N_(u"Spanish (Equador)"),
         "es_GT.UTF-8": N_(u"Spanish (Guatemala)"),
         "es_HN.UTF-8": N_(u"Spanish (Honduras)"),
         "es_MX.UTF-8": N_(u"Spanish (Mexico)"),
         "es_NI.UTF-8": N_(u"Spanish (Nicaragua)"),
         "es_PA.UTF-8": N_(u"Spanish (Panama)"),
         "es_PY.UTF-8": N_(u"Spanish (Paraguay)"),
         "es_PE.UTF-8": N_(u"Spanish (Peru)"),
         "es_PR.UTF-8": N_(u"Spanish (Puerto Rico)"),
         "es_ES.UTF-8": N_(u"Spanish (Spain) - Español"),
         "es_US.UTF-8": N_(u"Spanish (USA)"),
         "es_UY.UTF-8": N_(u"Spanish (Uruguay)"),
         "es_VE.UTF-8": N_(u"Spanish (Venezuela)"),
         "sv_FI.UTF-8": N_(u"Swedish (Finland)"),
         "sv_SE.UTF-8": N_(u"Swedish (Sweden) - Svenska"),
         "tl_PH": N_(u"Tagalog (Philippines)"),
         "ta_IN.UTF-8": N_(u"Tamil (India)"),
         "te_IN.UTF-8": N_(u"Telugu (India)"),
         "th_TH.UTF-8": N_(u"Thai"),
         "tr_TR.UTF-8": N_(u"Turkish"),
         "uk_UA.UTF-8": N_(u"Ukrainian"),
         "ur_PK": N_(u"Urdu (Pakistan)"),
         "uz_UZ": N_(u"Uzbek (Uzbekistan)"),
         "wa_BE@euro": N_(u"Walloon (Belgium)"),
         "cy_GB.UTF-8": N_(u"Welsh (Great Britain)"),
         "xh_ZA.UTF-8": N_(u"Xhosa (South Africa)"),
         "zu_ZA.UTF-8": N_(u"Zulu (South Africa)")
    }

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

    def get_locales_map(self):
        return self.__locales_map

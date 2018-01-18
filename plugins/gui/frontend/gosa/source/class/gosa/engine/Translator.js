/*
 * This file is part of the GOsa project -  http://gosa-project.org
 *
 * Copyright:
 *    (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de
 *
 * License:
 *    LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
 *
 * See the LICENSE file in the project's top-level directory for details.
 */

qx.Class.define("gosa.engine.Translator", {
  extend : qx.core.Object,
  type : "singleton",

  construct : function() {
    this.base(arguments);
    this._findRegEx = new RegExp('"\s*((trnc|trn|trc|tr|marktr)\\((.+?)\\))\s*"', "g");
    this._subRegEx = new RegExp("\s*(?:\"(.+?)\")|(?:'(.+?)')\s*", "g");
  },

  members : {
    _findRegEx : null,
    _subRegEx : null,

    translateJson : function(json) {
      qx.core.Assert.assertString(json);

      var match = this._findRegEx.exec(json);
      var subs;
      while (match) {
        subs = this._getSubstitution(match[2], match[3]);
        if (subs) {
          json = json.replace(match[1], subs);
        }
        match = this._findRegEx.exec(json);
      }
      return json;
    },

    _getSubstitution : function(trFun, args) {
      var parsedArgs = [];
      var match = this._subRegEx.exec(args);
      while (match) {
        parsedArgs.push(match[1] || match[2]);
        match = this._subRegEx.exec(args);
      }

      // TODO: allow trn and trnc
      var translation;
      switch (trFun) {
        case "tr":
          translation = qx.locale.Manager.tr.apply(undefined, parsedArgs);
          break;

        case "trc":
          translation = qx.locale.Manager.trc.apply(undefined, parsedArgs);
          break;

        case "marktr":
          // do not translate
          translation = parsedArgs[0];
          break;

        default:
          qx.log.Logger.warn("Translation function '" + trFun + "' is not implemented");
          break;
      }

      if (translation) {
        return translation.toString();
      }
      return null;
    }
  }
});

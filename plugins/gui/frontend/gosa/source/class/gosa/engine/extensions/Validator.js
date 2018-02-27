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

qx.Class.define("gosa.engine.extensions.Validator", {
  extend: qx.core.Object,

  implement : [gosa.engine.extensions.IExtension],

  statics : {
    FORM_VALIDATORS : {
    },

    WIDGET_VALIDATORS : {
      "5To120Letters" : function(value) {
        return typeof value === "string" && /^\w{5,120}$/.test(value.trim());
      }
    }
  },

  members : {

    process : function(data, target, context) {
      if (data.hasOwnProperty("target") && data.target === "form") {
        qx.core.Assert.assertKeyInMap("name", data);
        // add to global validation manager
        var clazz = qx.Class.getByName("gosa.engine.extensions.validators."+data.name);
        if (clazz) {
          var validator = new clazz();
          if (data.hasOwnProperty("properties")) {
            validator.set(data.properties);
          }
          context.setValidator(validator.validate);
          context.getValidationManager().setContext(validator);
        }
      }
      else if (target instanceof qx.ui.form.Form) {
        this._addFormValidator(data, target);
      }
      else if (target instanceof qx.ui.core.Widget) {
        this._addWidgetValidator(data, target);
      }
      else {
        qx.log.Logger.warn("No validation implemented for objects of type '" + target.classname + "'");
      }
    },

    _addFormValidator : function(data, target) {
      qx.core.Assert.assertString(data);

      var valManager = target.getValidationManager();
      var formValidators = this.self(arguments).FORM_VALIDATORS;

      if (!formValidators.hasOwnProperty(data)) {
        qx.log.Logger.error("Unknown validator: '" + data + "'");
        return;
      }
      valManager.setValidator(formValidators[data]);
    },

    _addWidgetValidator : function(data, target) {
      qx.core.Assert.assertObject(data);
      qx.core.Assert.assertKeyInMap("name", data);
      qx.core.Assert.assertKeyInMap("form", data);

      var widgetValidators = this.self(arguments).WIDGET_VALIDATORS;
      var formSymbol = data.form.trim().substring(1);
      if (!widgetValidators.hasOwnProperty(data.name)) {
        qx.log.Logger.error("Unknown validator: '" + data.name + "'");
        return;
      }
      var form = gosa.engine.SymbolTable.getInstance().resolveSymbol(formSymbol);
      form.getValidationManager().add(target, widgetValidators[data.name]);
    }
  },

  defer : function() {
    gosa.engine.ExtensionManager.getInstance().registerExtension("validator", gosa.engine.extensions.Validator);
  }
});

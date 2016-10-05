qx.Class.define("gosa.engine.extensions.Validator", {
  extend: qx.core.Object,

  implement : [gosa.engine.extensions.IExtension],

  statics : {
    FORM_VALIDATORS : {
      "userNameNotPrename" : function(widgets, form) {
        var prenameWidget, userNameWidget;
        widgets.forEach(function(widget) {
          var modelPath = widget.getUserData("modelPath");
          if (modelPath === "person.prename") {
            prenameWidget = widget;
          }
          else if (modelPath === "person.id") {
            userNameWidget = widget;
          }
        });

        qx.core.Assert.assertQxWidget(prenameWidget);
        qx.core.Assert.assertQxWidget(userNameWidget);
        var cond = prenameWidget.getValue() !== userNameWidget.getValue();
        if (!cond) {
          form.setInvalidMessage(qx.locale.Manager.tr("Prename and user name may not be the same."));
        }
        return cond;
      }
    },

    WIDGET_VALIDATORS : {
      "5To120Letters" : function(value) {
        return typeof value === "string" && /^\w{5,120}$/.test(value.trim());
      }
    }
  },

  members : {

    process : function(data, target) {
      if (target instanceof qx.ui.form.Form) {
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

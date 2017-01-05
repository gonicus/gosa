/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.engine.processors.FormProcessor", {
    extend : gosa.engine.processors.Base,

    members : {
      /**
       * @type {qx.ui.form.Form | null}
       */
      _form : null,

      /**
       * @type {qx.ui.form.renderer.IFormRenderer | null}
       */
      _formRenderer : null,

      process : function(node, target) {
        if (!target) {
          target = this._context.getRootWidget();
        }
        this._form = this._createNewForm(node, target);
        this._handleElements(node, this._form);
        this._createErrorArea();

        this._form.validate();
        this._form = null;
      },

      _createErrorArea : function() {
        var layout = new qx.ui.layout.Atom();
        layout.setCenter(true);
        var errorArea = new qx.ui.container.Composite(layout);
        errorArea.set({
          appearance : "error-box",
          visibility : "excluded"
        });
        var label = new qx.ui.basic.Label();
        errorArea.add(label);

        this._formRenderer.add(errorArea);
        this._form.getValidationManager().addListener("complete", function() {
          if (!this.isValid() && qx.lang.Array.contains(this.getInvalidMessages(), this.getInvalidMessage())) {
            errorArea.show();
            label.setValue(this.getInvalidMessage());
          }
          else {
            errorArea.exclude();
          }
        }, this._form.getValidationManager());
      },

      _createNewForm : function(node, target) {
        var form = new qx.ui.form.Form();
        var formWidget = this._formRenderer = this._addForm(node, target, form);

        var symbol = this._getValue(node, "symbol");
        if (symbol) {
          gosa.engine.SymbolTable.getInstance().addSymbol(symbol, form);
          gosa.engine.SymbolTable.getInstance().addSymbol(symbol + "Widget", formWidget);
        }
        this._handleExtensions(node, form);

        return form;
      },

      _addForm : function(node, target, form) {
        var groupBox = new qx.ui.groupbox.GroupBox(this._getValue(node, "label"));
        groupBox.setLayout(new qx.ui.layout.VBox());

        var rendererClazz = qx.Class.getByName(this._getValue(node, "renderer"));
        groupBox.add(new rendererClazz(form));

        if (target) {
          target.add(groupBox);
        }
        return groupBox;
      },

      _handleElements : function(node, target) {
        var elements = this._getValue(node, "elements");
        if (elements) {
          elements.forEach(function(element) {
            this._handleElement(element, target);
          }, this);
        }
      },

      _handleElement : function(node, target) {
        var group = this._getValue(node, "group");
        if (group) {
          target.addGroupHeader(group);
        }
        else {
          var widget = this._addFormWidget(node, target);
          this._handleVisibility(node, widget);
        }
      },

      _addFormWidget : function(node, target) {
        var clazz = qx.Class.getByName(this._getValue(node, "class"));
        qx.core.Assert.assertNotUndefined(clazz, "Unknown class: '" + this._getValue(node, "class") + "'");

        var widget = new clazz();
        if (widget instanceof qx.ui.form.AbstractField) {
          widget.setLiveUpdate(true);
        }
        widget.addListener("changeValue", this._form.validate, this._form);

        var properties = this._getValue(node, "properties");
        if (properties) {
          widget.set(this._transformProperties(properties));
        }

        var modelPath = this._getValue(node, "modelPath");
        if (modelPath) {
          widget.setUserData("modelPath", modelPath);
          gosa.engine.WidgetRegistry.getInstance().addWidget(this._getValue(node, "modelPath"), widget);
        }

        var symbol = this._getValue(node, "symbol");
        if (symbol) {
          gosa.engine.SymbolTable.getInstance().addSymbol(symbol, widget);
        }

        this._handleExtensions(node, widget);

        target.add(widget, this._getValue(node, "label"));
        return widget;
      },

      _handleVisibility : function(node, target) {
        var dependsOn = this._getValue(node, "visibilityDependsOn");
        if (dependsOn) {
          dependsOn = dependsOn.trim();
          // negation
          var negated = false;
          if (dependsOn.startsWith("!")) {
            negated = true;
            dependsOn = dependsOn.substring(1);
          }

          var source = this._resolveSymbol(dependsOn);
          if (negated) {
            source.bind("value", target, "visibility", {
              converter : function(value) {
                return value ? "excluded" : "visible";
              }
            });
          }
          else {
            source.bind("value", target, "visibility", {
              converter : function(value) {
                return value ? "visible" : "excluded";
              }
            });
          }
        }
      }
    }
});

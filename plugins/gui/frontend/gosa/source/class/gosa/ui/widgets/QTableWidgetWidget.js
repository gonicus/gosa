/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/* This class is a qooxdoo-widget representation of the cure-QtableWidget.
 *
 * Notice that this plugin can occure in two different forms.
 *
 * 1. The first form is a table like widget as used on the PosixUser-tab
 *    It allows to select multiple values for a single property.
 * 2. The other form is a single-select widget, which looks similar to a
 *    normal TextField. It only allows to select a single value.
 *    This is used for the User's manager attribute or the SambaUser's
 *    primaryGroupSID
 *
 * */
qx.Class.define("gosa.ui.widgets.QTableWidgetWidget", {

  extend: gosa.ui.widgets.Widget,

  construct: function(){
    this.base(arguments);
    this.contents.setLayout(new qx.ui.layout.Canvas());
    var attrs = ["buddyOf","attribute",
          "labelText","extension","guiProperties","caseSensitive",
          "blockedBy","defaultValue","dependsOn","mandatory",
          "type","unique","values","readOnly","multivalue",
          "initComplete", "enabled",
          "value","required","placeholder","maxLength","modified"];

    this.contents.add(new qx.ui.core.Spacer(1), {left:0, right:0, bottom: 0, top:0});

    this.addListenerOnce("appear", function() {
      // Create the multi-select style widget or the single select widget depending on the source-properties multivalue
      // state.

      var widget;
      if (this.isMultivalue()) {
        widget = new gosa.ui.widgets.TableWithSelector();
      } else {
        widget = new gosa.ui.widgets.SingleSelector();
      }

      widget.addListener("changeValue", function(e){
        this.fireDataEvent("changeValue", e.getData());
      }, this);

      for (var attr in attrs){
        this.bind(attrs[attr], widget, attrs[attr]);
      }

      this.contents.add(widget, {left:0, right:0, bottom: 0, top:0});
      this._widget = widget;
    }, this);
  },

  destruct: function(){

    // Remove all listeners and then set our values to null.
    qx.event.Registration.removeAllListeners(this);

    this._disposeObjects("_widget");
  },

  statics: {

    /* Create a readonly representation of this widget for the given value.
     * This is used while merging object properties.
     * */
    getMergeWidget: function(value){
      var container = new qx.ui.container.Composite(new qx.ui.layout.VBox());
      for(var i=0;i<value.getLength(); i++){
        var w = new qx.ui.form.TextField(value.getItem(i));
        w.setReadOnly(true);
        container.add(w);
      }
      return(container);
    }
  },

  members: {

    _widget: null,

    /* Sets an error message for the widget given by id.
     */
    setErrorMessage: function(message, id){
      this._widget.setErrorMessage(message, id);
    },

    /* Resets error messages
     * */
    resetErrorMessage: function(){
      if(this._widget){
        this._widget.resetErrorMessage();
      }
    }
  }
});

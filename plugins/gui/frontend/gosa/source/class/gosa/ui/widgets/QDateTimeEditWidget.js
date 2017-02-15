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

qx.Class.define("gosa.ui.widgets.QDateTimeEditWidget", {

  extend : gosa.ui.widgets.QDateEditWidget,

  statics: { 
 
    /* Create a readonly representation of this widget for the given value. 
     * This is used while merging object properties. 
     * */ 
    getMergeWidget: function(value){ 
      var w = new gosa.ui.widgets.DateTimeField();
      w.setEnabled(false); 
      if(value.getLength()){
        w.setValue(value.getItem(0).get());
      }
      return(w);
    }
  },

  members: {
 
    /* Creates an input-widget and connects the update listeners
     * */
    _createWidget: function(){
      var w = new gosa.ui.widgets.DateTimeField();

      if(this.getPlaceholder()){
        w.setPlaceholder(this.getPlaceholder());
      }
      if(this.getPlaceholder()){
        w.setPlaceholder(this.getPlaceholder());
      }
      w.addListener("changeValue", function(){
          this.addState("modified");
          this._propertyUpdater();
        }, this);
      this.bind("valid", w, "valid");
      this.bind("invalidMessage", w, "invalidMessage");
      return(w);
    }
  }
});

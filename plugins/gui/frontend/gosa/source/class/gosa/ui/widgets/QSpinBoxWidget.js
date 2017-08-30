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

qx.Class.define("gosa.ui.widgets.QSpinBoxWidget", {

  extend: gosa.ui.widgets.MultiEditWidget,

  construct: function(){
    this.base(arguments);
  },

  statics: {
    
    /**
     * Create a readonly representation of this widget for the given value.
     * This is used while merging object properties.
     */
    getMergeWidget: function(value){
      var container = new qx.ui.container.Composite(new qx.ui.layout.VBox());
      for(var i=0;i<value.getLength(); i++){
        var w = new qx.ui.form.TextField(value.getItem(i) + "");
        w.setReadOnly(true);
        container.add(w);
      }
      return(container);
    }
  },    

  properties: {
  
    maximum: {
      check : "Number",
      init : 100000,
      event: "changeMaximum"
    },

    minimum: {
      check : "Number",
      init : -1,
      event: "changeMinimum"
    }
  },

  members: {
 
    _default_value: 0,

    /**
     * Apply collected gui properties to this widet
     */
    _applyGuiProperties: function(props){

      // This happens when this widgets gets destroyed - all properties will be set to null.
      if(!props){
        return;
      }

      if(props["placeholderText"] && props["placeholderText"]["string"]){
        this.setPlaceholder(props["placeholderText"]["string"]);
      }
      if(props["maximum"] && props["maximum"]["number"]){
        this.setMaximum(parseInt(props["maximum"]["number"])) ;
      }
      if(props["minimum"] && props["minimum"]["number"]){
        this.setMinimum(parseInt(props["minimum"]["number"])) ;
      }
    },

    /* Creates an input-widget depending on the echo mode (normal/password)
     * and connects the update listeners
     * */
    _createWidget: function(){
      var w = new gosa.ui.form.Spinner();
      if(this.getPlaceholder()){
        w.setPlaceholder(this.getPlaceholder());
      }
      w.addListener("changeValue", function(){
          this.addState("modified");
          this._propertyUpdater();
        }, this); 
      this.bind("maximum", w, "maximum");
      this.bind("minimum", w, "minimum");
      w.bind("backgroundColor", w.getChildControl("textfield"), "backgroundColor");
      this.bind("valid", w, "valid");
      this.bind("invalidMessage", w, "invalidMessage");
      return(w);
    }
  }
});

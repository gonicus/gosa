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

/* This is the base class for all input-widgets created by
 * the Renders class.
 *
 * It contains all necessary properties/methods and events to bind values,
 * set error messages, set placeholder...
 * */
qx.Class.define("gosa.ui.widgets.Widget", {

  extend: qx.ui.container.Composite,

  construct: function(){
    this.base(arguments);
    this.name = this.classname.replace(/^.*\./, "");
    this.addState("gosaWidget");
    this.addState("gosaInput");
    this.setLayout(new qx.ui.layout.Canvas());
    this.contents = new qx.ui.container.Composite();
    this.add(this.contents, {top:0, left:0, bottom:0, right:0});
    this.setFocusable(false);
    this.setValue(new qx.data.Array());
  },

  destruct: function(){

    // Remove all listeners and then set our values to null.
    qx.event.Registration.removeAllListeners(this);

    this.setBuddyOf(null);
    this.setGuiProperties(null);
    this.setValues(null);
    this.setValue(null);
    this.setBlockedBy(null);
  },

  properties : {

    buddyOf: {
      init: null,
      event: "_buffyOfChanged",
      check: "qx.ui.core.Widget",
      nullable: true
    },

    valid: {
      check: "Boolean",
      event: "_validChanged",
      init: true,
      apply: "_applyValid"
    },

    invalidMessage: {
      check: "String",
      event: "_invalidMessageChanged",
      init: ""
    },

    attribute: {
      check: "String",
      event: "_attributeChanged",
      init: ""
    },

    widgetName: {
      check: "String",
      event: "_widgetNameChanged",
      init: ""
    },

    labelText: {
      check: "String",
      event: "_labelTextChanged",
      init: ""
    },

    extension: {
      check: "String",
      event: "_extensionChanged",
      init: ""
    },

    guiProperties: {
      apply: "_applyGuiProperties",
      event: "_guiPropertiesChanged",
      init: null,
      nullable: true
    },

    caseSensitive: {
      event: "_caseSensitiveChanged",
      init: false
    },

    blockedBy: {
      event: "_blockedByChanged",
      check: "Array",
      nullable: true,
      init: null
    },

    blocked: {
      event: "_blockedChanged",
      check: "Boolean",
      nullable: true,
      init: false
    },

    defaultValue: {
      init: null,
      event: "_defaultValueChanged",
      nullable: true
    },

    dependsOn: {
      init: null,
      event: "_dependsOnChanged",
      nullable: true
    },

    mandatory: {
      check: "Boolean",
      init: false,
      event: "_mandatoryChanged",
      apply: "_applyMandatory"
    },

    type: {
      event: "_typeChanged",
      init: false
    },

    unique: {
      event: "_uniqueChanged",
      init: false
    },

    parent: {
      event: "_parentChanged",
      init: null
    },

    tabStopIndex: {
      event: "_changedTabStopIndex",
      apply: "_applyTabStopIndex",
      init: 1
    },

    /* The values to display as selectables in the dropdown box
     * */
    values: {
      apply : "_applyValues",
      event: "_valuesChanged",
      nullable: true,
      init : null
    },

    /* Whether the widget is a read only
     * */
    readOnly : {
      check : 'Boolean',
      apply: '_applyReadOnly',
      event: "_readOnlyChanged",
      init: false
    },

    /* Whether the widget is a multi-value input or not.
     * */
    multivalue : {
      check : 'Boolean',
      apply: '_applyMultivalue',
      event: "_multivalueChanged",
      init: false
    },

    /* The value(s) for the widget.
     * All values (each when not multivalue) are of type qx.data.Array.
     * */
    value : {
      init : null,
      check : "qx.data.Array",
      nullable: true,
      event: 'changedValue',
      apply: '_applyValue'
    },

    /* Whether the field is required or not.
     * */
    required : {
      init : false,
      check : 'Boolean',
      nullable: false,
      event: "_requiredChanged",
      apply: '_applyRequired'
    },

    /* The placeholder to use.
     * */
    placeholder : {
      init : "",
      event: "_placeholderChanged",
      nullable: true
    },

    /* The maximum length
     * */
    maxLength : {
      init : null,
      check : "Integer",
      event: "_maxLengthChanged",
      nullable: true
    },

    /* Whether the widget was modified
     * */
    modified : {
      init : false,
      event: "_modifiedChanged",
      check : "Boolean"
    },

    /* Is set to true once the renderer has finished
     * preparing this widget
     * */
    initComplete : {
      check : 'Boolean',
      event: "initCompleteChanged",
      apply: "_initComplete",
      init: false
    }
  },

  events: {
    "changeValue" : "qx.event.type.Data"
  },

  statics: {

    /* Create a readonly representation of this widget for the given value.
     * This is used while merging object properties.
     * */
    getMergeWidget: function(value){
      var w = new qx.ui.form.TextField();
      w.setReadOnly(true);
      if(value.getLength()){
        w.setValue(value.getItem(0) + "");
      }
      return(w);
    }
  },

  members: {

    name: null,
    contents: null,
    _default_value: null,

    /* Enforce property update
     * */
    enforceUpdateOnServer: function(){
      this.fireDataEvent("changeValue", this.getCleanValues());
    },

    /* Returns the widget values in a clean way,
     * to avoid saving null or empty values for an object
     * property.
     * */
    getCleanValues: function()
    {
      var data = new qx.data.Array();
      for(var i=0; i<this._current_length; i++){
        var val = this._getWidgetValue(i);
        if(val !== null && val !== this._default_value){
          data.push(val);
        }
      }
      return(data);
    },

    /* Block the widget and disable modifications
     * */
    block: function(){
      this.exclude();
      this.setBlocked(true);
      if(this.getBuddyOf()){
        this.getBuddyOf().exclude();
      }
    },

    /* Unblock the widget
     * */
    unblock: function(){
      this.show();
      this.setBlocked(false);
      if(this.getBuddyOf()){
        this.getBuddyOf().show();
      }
    },

    // property apply
    _applyMandatory : function() {
    },

    /* Apply collected gui properties to this widget
     * */
    _applyGuiProperties: function(props){
      if(!props){
        return;
      }

      // Call a remote method to get the widgets value
      if(props.callObjectMethod && props.callObjectMethod){
        this.setValue(new qx.data.Array([this.tr("Pending...")]));
        this.addListener('appear', function(){
          var method_signature = props.callObjectMethod;
          var splitter = /([^(]+)\(([^)]*)\)/;
          var info = splitter.exec(method_signature);
          var _args = info[2].split(",");
          var args = [];
          for (var i= 0; i<_args.length; i++) {
            var tmp = _args[i].trim();
            if (tmp == "%locale") {
              args.push(gosa.Tools.getLocale());
            } else {
              args.push(tmp);
            }
          }

          var controller = this._getController();
          controller.callObjectMethod(info[1], args)
          .then(function(result) {
            this.setValue(new qx.data.Array([result]));
          }, this)
          .catch(function(error) {
            this.error("failed to call method '" + props["callObjectMethod"]["string"] + "'");
            this.error(error);
            this.setValue(new qx.data.Array([this.tr("Failed...")]));
          }, this);
        }, this);
      }

      if(props["placeholderText"] && props["placeholderText"]["string"]){
        this.setPlaceholder(this['tr'](props["placeholderText"]["string"]));
      }
      if(props["echoMode"] && props["echoMode"]["enum"]){
        var echomode = props["echoMode"]["enum"];
        if (echomode == "QLineEdit::Password") {
          this.setEchoMode('password');
        } else if (echomode == "QLineEdit::NoEcho") {
          this.error("*** TextField NoEcho not supported!");
          return null;
        } else if (echomode == "QLineEdit::PasswordEchoOnEdit") {
          this.error("*** TextField NoEcho not supported!");
          return null;
        }
      }
      if(props["maxLength"] && props["maxLength"]["number"]){
        this.setMaxLength(parseInt(props["maxLength"]["number"])) ;
      }
    },

    _getController : function() {
      var widget = this;
      do {
        if (widget.getController) {
          return widget.getController();
        }
        widget = widget.getLayoutParent();
      } while (widget);
      return null;
    },

    shortcutExecute : function(){},

    _applyReadOnly: function(bool)
    {
      this.setEnabled(!bool);
    },

    _applyRequired: function(bool){
    },

    _applyValues: function(){},

    /* Apply method prototypes...
     * */
    focus:  function(){
    },

    _applyValue: function(value, oldValue) {
    },

    _applyMultivalue: function(value){
    },

    _applyValid : function(value) {
      if (value) {
        this.removeState("invalid");
      }
      else {
        this.addState("invalid");
      }
    },

    _applyTabStopIndex: function(value){
    },

    _initComplete: function() {
      this.getChildren().forEach(function(child) {
        if (child instanceof gosa.ui.widgets.Widget) {
          child.setInitComplete(this.getInitComplete());
        }
      }, this);
    },

    /**
     * Resets error messages
     */
    resetErrorMessage: function(){
      this.setInvalidMessage("");
      this.setValid(true);
    },

    /**
     * Parses an incoming error-object and then sets the error message.
     * @param error_object {Error}
     */
    setError: function(error_object){
      var message = error_object.text;
      if(error_object.details){
        for(var i=0; i< error_object.details.length; i++){
          this.setErrorMessage(message + " - " + error_object.details[i].detail, error_object.details[i].index);
        }
      }else{
        this.setErrorMessage(message, 0);
      }
    },

    /**
     * Sets an error message for the widget given by id.
     * @param message {String}
     * @param id {Number} widget id
     */
    setErrorMessage: function(message, id){
      this.setInvalidMessage(message);
      this.setValid(false);
    }
  }
});

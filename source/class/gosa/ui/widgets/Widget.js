/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/* This is the base class for all input-widgets created by 
 * the Renders class.
 *
 * It contains all necessary properties/methods and events to bind values,
 * set error messages, set placeholder...
 * */
qx.Class.define("gosa.ui.widgets.Widget", {

  extend: qx.ui.container.Composite,

  construct: function(){
    this.name = this.classname.replace(/^.*\./, "");
    this.base(arguments);  
    this.setValue(new qx.data.Array());
    this.setFocusable(true);

    this.addState("gosaWidget");
    this.addState("gosaInput");
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
      init: true
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
    }
  },

  events: {
    "changeValue" : "qx.event.type.Data"
  },

  members: {

    name: null,


    /* Block the widget and disable modifications
     * */
    block: function(){
      this.exclude();
      if(this.getBuddyOf()){
        this.getBuddyOf().exclude();
      }
    },

    /* Unblock the widget
     * */
    unblock: function(){
      this.show();
      if(this.getBuddyOf()){
        this.getBuddyOf().show();
      }
    },

    /* Apply collected gui properties to this widet
     * */
    _applyGuiProperties: function(props){
      if(!props){
        return;
      }

      if(props["placeholderText"] && props["placeholderText"]["string"]){
        this.setPlaceholder(this.tr(props["placeholderText"]["string"]));
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

    _applyValue: function(value){
    },

    _applyMultivalue: function(value){
    },

    _applyMandatory: function(value){
    },
 

    /* Resets error messages
     * */
    resetErrorMessage: function(){
      this.setInvalidMessage("");
      this.setValid(true);
    },

    /* Parses an incoming error-object and then sets the error message.
     * */
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

    /* Sets an error message for the widget given by id.
     */ 
    setErrorMessage: function(message, id){
      this.setInvalidMessage(message);
      this.setValid(false);
    }
  }
});

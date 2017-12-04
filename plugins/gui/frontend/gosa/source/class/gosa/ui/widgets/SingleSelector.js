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

qx.Class.define("gosa.ui.widgets.SingleSelector", {

  extend: gosa.ui.widgets.Widget,

  include: gosa.ui.widgets.MDragDrop,

  construct: function(valueIndex){

    this.base(arguments, valueIndex);
    this.contents.setLayout(new qx.ui.layout.HBox(0));
    this._columnNames = [];
    this._columnIDs = [];
    this._resolvedNames = {};

    // Create the gui on demand
    this.addListenerOnce("initCompleteChanged", function() {
      this._createGui();
      this.__updateVisibleText();
    }, this);
  },

  destruct: function(){

    // Remove all listeners and then set our values to null.
    qx.event.Registration.removeAllListeners(this);

    this.setBuddyOf(null);
    this.setGuiProperties(null);
    this.setValues(null);
    this.setValue(null);
    this.setBlockedBy(null);

    this._disposeObjects("_table", "_actionBtn", "_widget", "_tableModel");

    this._tableData = null;
    this._columnNames = null;
    this._editTitle = null;
    this._columnIDs = null;
    this._firstColumn = null;
    this._resolvedNames = null;
  },

  members: {

    _initially_set: false,
    _initially_send_update: true,

    _table: null,
    _tableModel: null,
    _tableData: null,
    _columnNames: null,
    _editTitle: "",
    _columnIDs: null,
    _firstColumn: null,
    _resolvedNames: null,
    _widget: null,
    _actionBtn: null,

    /* Color the specific row red, if an error occurred!
     */
    setErrorMessage: function(message, id){
      this.setValid(false);
      this.setInvalidMessage(message);
    },

    /**
     * Resets error messages
     */
    resetErrorMessage: function(){
      this.setInvalidMessage("");
      this.setValid(true);
    },

    /**
     * Applies the widget value and updates the visible text
     */
    _applyValue: function(value){

      // This happens when this widgets gets destroyed - all properties will be set to null.
      if(value === null){
        return;
      }

      this.__updateVisibleText();

      // Send initial content to process validators"
      if(this._initially_set && this._initially_send_update){
        this.fireDataEvent("changeValue", value.copy());
        this._initially_send_update = false;
      }
      this._initially_set = true;
    },

    /**
     * Updates the visible text of the widgets.
     * If it cannot, eg. some values are still not fetched from the backend
     * then it enforces a rpc request to fetch those.
     */
    __updateVisibleText: function(){
      if(this._widget){
        if(this.getValue().getLength()){
          var name = this.getValue().getItem(0);
          if(name in this._resolvedNames){
            this._widget.setValue(this._resolvedNames[name][this._firstColumn]);
          }else{
            this._widget.setValue(this.tr("loading") + "...");
            this.__resolveMissingValues();
          }
        }else{
          this._widget.setValue("");
        }
      }

      // Update buttons
      if(this._actionBtn){
        if(this.getValue().getLength()){
          this._actionBtn.setIcon("@Ligature/trash/22");
          this._actionBtn.setToolTip(new qx.ui.tooltip.ToolTip(this.tr("Remove value")));
        }else{
          this._actionBtn.setIcon("@Ligature/folder/22");
          this._actionBtn.setToolTip(new qx.ui.tooltip.ToolTip(this.tr("Choose value")));
        }
      }
    },


    /**
     * Creates the gui element of this widget
     */
    _createGui: function(){
      this._widget = new qx.ui.form.TextField();
      this._widget.setReadOnly(true);

      this._actionBtn = new qx.ui.form.Button(null, "@Ligature/folder/22").set({
            "padding": 2,
            "margin": 0
            });
      this._actionBtn.setAppearance("button-link");
      this._actionBtn.setToolTip(new qx.ui.tooltip.ToolTip(this.tr("Choose value")));
      this._actionBtn.setFocusable(false);

      this.contents.add(this._widget, {flex: 1});
      this.contents.add(this._actionBtn);

      this.bind("valid", this._widget, "valid");
      this.bind("invalidMessage", this._widget, "invalidMessage");

      // Act on button clicks here, remove the value or allow to select a new one
      this._actionBtn.addListener("execute", function(){

          // There is already a value, remove it
          var value = this.getValue();
          if (value.getLength()) {
            value.removeAll();
            this._applyValue(value);
            this.fireDataEvent("changeValue", this.getValue().copy());
          }
          else {
            this.__openSelectionDialog();
          }
        }, this);

     this._initDragDropListeners();
    },

    _onDropRequest: function(e) {
      var action = e.getCurrentAction();
      var type = e.getCurrentType();

      if (type === this.getDragDropType()) {

        var value = this.getValue().getItem(0);

        if (action === "move") {
          this.getValue().removeAll();
          this.__updateVisibleText();
        }

        e.addData(this.getDragDropType(), value);
      }
    },

    __openSelectionDialog : function() {
      var d = new gosa.ui.dialogs.ItemSelector(
        this['tr'](this._editTitle),
        this.getValue().toArray(),
        this.getExtension(),
        this.getAttribute(),
        {
          ids : this._columnIDs,
          names : this._columnNames
        },
        true
      );

      d.addListener("selected", function(e){
        if (e.getData().length) {
          this.getValue().removeAll();
          this.getValue().push(e.getData()[0]);
          this.fireDataEvent("changeValue", this.getValue().copy());
          this.__resolveMissingValues();
        }
      }, this);

      d.open();
    },

    onDrop: function(ev) {
      if (ev.supportsType(this.getDragDropType())) {
        var items = ev.getData(this.getDragDropType());
        var values = this.getValue();
        values.removeAll();
        items.forEach(function(entry) {
          if (!values.contains(entry)) {
            values.push(entry);
          }
        });
        if (items.length) {
          this.fireDataEvent("changeValue", values.copy());
          this.__resolveMissingValues();
        }
      }
    },

    /**
     * Resolve missing value information
     */
    __resolveMissingValues: function(){

      var rpc = gosa.io.Rpc.getInstance();
      var values = this.getValue().toArray();

      var unknown_values = [];
      for(var i=0; i<values.length; i++){
        if(!(values[i] in this._resolvedNames)){
          unknown_values.push(values[i]);

          var row_data = {};
          row_data[this._firstColumn] = values[i];
          row_data["__identifier__"] = values[i];
          this._resolvedNames[values[i]] = row_data;
        }
      }

      if (unknown_values.length) {
        rpc.cA("getObjectDetails", this.getExtension(), this.getAttribute(), unknown_values, this._columnIDs)
        .then(function(result) {
          for(var value in result['map']){
            var data = result['result'][result['map'][value]];
            if(data){
              data['__identifier__'] = value;
              this._resolvedNames[value] = data;
            }
          }
          this.__updateVisibleText();
        }, this)
        .catch(function(error) {
          new gosa.ui.dialogs.Error(error).open();
        });
      } else {
        this.__updateVisibleText();
      }
    },


    /**
     * Apply properties that were defined in the ui template.
     *
     * Collect column names here.
     */
    _applyGuiProperties: function(props){

      // This happens when this widgets gets destroyed - all properties will be set to null.
      if(!props){
        return;
      }

      if('editTitle' in props){
        this._editTitle = props['editTitle'];
      }
      this._columnNames = [];
      this._columnIDs = [];
      var first = null;
      if('columns' in props){
        for(var col in props['columns']){
          this._columnNames.push(props['columns'][col]);
          this._columnIDs.push(col);
          if(!first){
            first = col;
          }
        }
      }
      this._firstColumn = first;

      this._applyDragDropGuiProperties(props);
    }
  }
});

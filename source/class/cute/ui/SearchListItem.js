qx.Class.define("cute.ui.SearchListItem", {

  extend: qx.ui.core.Widget,
  implement : [qx.ui.form.IModel],
  include : [qx.ui.form.MModelProperty],

  construct: function(){
    this.base(arguments);
    this._setLayout(new qx.ui.layout.Grid(0));
  },

  properties: {
    dn :
    {
      apply : "_applyDn",
      nullable : true,
      check : "String",
      event : "changeDn"
    },

    description :
    {
      apply : "_applyDescription",
      nullable : true,
      check : "String",
      event : "changeDescription"
    },

    icon :
    {
      apply : "_applyIcon",
      nullable : true,
      check : "String",
      event : "changeIcon"
    },

    title :
    {
      apply : "_applyTitle",
      nullable : true,
      check : "String",
      event : "changeTitle"
    }
  },

  members:{
 

    _applyTitle: function(){
      this._showChildControl("title");
    },

    _applyIcon: function(){
      this._showChildControl("icon");
    },

    _applyDescription: function(){
      this._showChildControl("description");
    },

    _applyDn: function(value){
      this._showChildControl("dn");
    },

    _createChildControlImpl : function(id, hash)
    {
      var control;

      switch(id)
      {
        case "dn":
          control = new qx.ui.basic.Label(this.getDn());
          this._add(control, {row: 0, column: 0});
          break;
        case "title":
          control = new qx.ui.basic.Label(this.getTitle());
          this._add(control, {row: 1, column: 0});
          break;
        case "icon":
          control = new qx.ui.basic.Label(this.getIcon());
          this._add(control, {row: 2, column: 0});
          break;
        case "description":
          control = new qx.ui.basic.Label(this.getDescription());
          this._add(control, {row: 3, column: 0});
          break;
      }
      return control || this.base(arguments, id);
    }
  }
});

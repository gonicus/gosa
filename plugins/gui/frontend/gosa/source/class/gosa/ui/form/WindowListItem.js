

qx.Class.define("gosa.ui.form.WindowListItem", {
  extend: qx.ui.form.ListItem,

  /*
  *****************************************************************************
     CONSTRUCTOR
  *****************************************************************************
  */
  construct : function() {
    this.base(arguments);
    this.addListener("changeModel", this._onChangeModel, this);
  },

  /*
  *****************************************************************************
     PROPERTIES
  *****************************************************************************
  */
  properties : {
    appearance :
    {
      refine : true,
      init : "gosa-listitem-window"
    },

    window: {
      check: "qx.ui.window.Window",
      nullable: true
    }
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {
    _onChangeModel: function(ev) {
      var model = ev.getData();
      if (model) {
        var dnPart = qx.util.StringSplit.split(qx.util.StringSplit.split(model.dn, "\,")[0], "=")[1];
        this.setLabel(dnPart);
      }
    }
  }
});
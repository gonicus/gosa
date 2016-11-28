

qx.Class.define("gosa.ui.form.WindowListItem", {
  extend: qx.ui.form.ListItem,

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
    },

    object: {
      check: "gosa.proxy.Object",
      async: true,
      nullable: true,
      apply: "_applyObject"
    }
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {
    _applyObject: function(object) {
      if (object) {
        // try to get the search result for this dn, to get the mapped title/icon values
        return gosa.io.Rpc.getInstance().cA("getObjectSearchItem", object.dn)
        .then(function(result) {
          this.setLabel(result.title);
          this.setIcon(result.icon ? result.icon : gosa.util.Icons.getIconByType(result.tag, 22));
        }, this)
        .catch(function(error) {
          this.error(error);
          // fallback
          var dnPart = qx.util.StringSplit.split(qx.util.StringSplit.split(object.dn, "\,")[0], "=")[1];
          this.setLabel(dnPart);
        }, this);

      }
    }
  }
});
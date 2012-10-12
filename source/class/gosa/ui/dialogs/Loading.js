qx.Class.define("gosa.ui.dialogs.Loading",
{
  extend : gosa.ui.dialogs.Dialog,

  construct : function()
  {
    this.base(arguments, "GOsa - " + this.tr("Initializing") + "...");
    this.label = new qx.ui.basic.Label();
    this.add(this.label);
  },

  members: {
    label: null,
    setLabel: function(action){
      this.label.setValue(action);
    }
  }
});


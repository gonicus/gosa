qx.Class.define("cute.ui.dialogs.Loading",
{
  extend : cute.ui.dialogs.Dialog,

  construct : function()
  {
    this.base(arguments, this.tr("Initializing") + "...");
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


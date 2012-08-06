qx.Class.define("cute.ui.dialogs.Dialog",
{
  extend : qx.ui.window.Window,

  construct : function(caption, icon)
  {
    this.base(arguments, caption, icon);
    this.setModal(true);
    this.addListener("appear", function(){
        this.center(); 
      }, this);

    this.setMinWidth(300);
    this.setMinHeight(120);
  }
});

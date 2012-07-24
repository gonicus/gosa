qx.Class.define("cute.ui.widgets.Upload",
{
  extend : qx.ui.core.Widget,

  events : {
    "selected": "qx.event.type.Event"
  },

  members :
  {
    element: null,

    click: function(){
      this.element.getDomElement().click();
    },

    _createContentElement : function()
    {
      var el = new qx.html.Element(
        "input",
        {
          overflowX: "hidden",
          overflowY: "hidden"
        },
        {
          type: "file"
        }
      );
      this.element = el;
      el.addListener("change", function(){ 
          this.fireEvent("selected");
        }, this);
      return(el);
    }, 

    getFile : function() {
      return(qx.bom.FileReader.getFile(this.getContentElement().getDomElement(), 0));
    }
  }
});


/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.ui.Header", {

  extend: qx.ui.container.Composite,

  construct: function() {
    this.base(arguments);
    this.setLayout(new qx.ui.layout.Canvas());

    this._createChildControl("logo");
    this._createChildControl("label");
    this._createChildControl("logout");
  }, 

  properties: {

    appearance: {
      refine: true,
      init: "title-bar"
    },
  
    loggedInName: {
      init: "",
      check: "String",
      event: "_changedLoggedInName",
      nullable: true,
      apply: "setLoggedInName"
    }
  },

  members: {

    _createChildControlImpl: function(id) {
      var control;
      switch(id) {

        case "container":
          control = new qx.ui.container.Composite(new qx.ui.layout.HBox(10));
          this.add(control, {top:0, bottom:0, right: 10});
          break;

        case "logo":
          control = new qx.ui.basic.Atom();
          this.add(control, {top:0, left:0, bottom: 0, right: 0});
          break;

        case "label":
          control = new qx.ui.basic.Label("");
          control.setToolTip(new qx.ui.tooltip.ToolTip(this.tr("Edit your profile")));
          control.setRich(true);
          this.getChildControl("container").add(control);

          control.addListener("click", function(){
            document.location.href = gosa.Tools.createActionUrl('openObject', gosa.Session.getInstance().getUuid());
          }, this);
          break;

        case "logout":
          control = new qx.ui.basic.Image();
          control.setToolTip(new qx.ui.tooltip.ToolTip(this.tr("Logout")));
          control.addListener("click", function(){
            gosa.Session.getInstance().logout();
          }, this);
          this.getChildControl("container").add(control);
          break;
      }

      return control || this.base(arguments, id);
    },

    setLoggedInName: function(value){
      if(value === null){
        this.getChildControl("label").setValue("");
      }else{
        this.getChildControl("label").setValue("<b>" + this.tr("Logged in:") + "</b> " + value);
      }
    }
  }
});

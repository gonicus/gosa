/**
 * Options for the layout of a widget that cannot be made via "layoutConfig" in the json template.
 */
qx.Class.define("gosa.engine.extensions.LayoutOptions", {
  extend: qx.core.Object,

  implement : [gosa.engine.extensions.IExtension],

  members : {

    process : function(data, target) {
      qx.core.Assert.assertObject(data);
      qx.core.Assert.assertQxWidget(target);

      if (data.hasOwnProperty("columnFlex")) {
        var flexConfig = data.columnFlex;
        qx.core.Assert.assertKeyInMap("column", flexConfig);
        qx.core.Assert.assertKeyInMap("flex", flexConfig);

        // one or several columns?
        if (typeof flexConfig.column === "object") {
          for (var i=0; i < flexConfig.column.length; i++) {
            target.getLayout().setColumnFlex(flexConfig.column[i], flexConfig.flex);
          }
        }
        else {
          target.getLayout().setColumnFlex(flexConfig.column, flexConfig.flex);
        }
      }
    }
  },

  defer : function() {
    gosa.engine.ExtensionManager.getInstance().registerExtension("layoutOptions", gosa.engine.extensions.LayoutOptions);
  }
});

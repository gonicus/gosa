/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */
/**
 * Dialog window that can show several widgets to merge the value of an attribute.
 */
qx.Class.define("gosa.ui.dialogs.MergeDialog", {

  extend: gosa.ui.dialogs.Dialog,

  include : [gosa.data.MBidirectionalBinding],

  construct: function(mods, exts, blocks, extDependencies, order) {
    this.base(arguments, this.tr("Merge required"));
    this.set({
      resizable : true,
      width : 700,
      height : 500,
      autoDispose : true
    });

    var layout = new qx.ui.layout.Grid(15, 15);
    layout.setColumnFlex(1, 1);
    layout.setColumnFlex(2, 2);
    layout.setColumnFlex(3, 2);
    var changesPane = new qx.ui.container.Composite(layout);

    var mergeWidgets = this.__mergeWidgets = {};
    var row = 0;
    var itemId = 0;
    var callOnce = [];
    var extList = {};
    var selections = [];
    var extensions = [];
    var items = {};
    var that = this;
    var firstAttr = true;
    var firstExt = true;

    // This method adds a new merge-selector for a property.
    var createSelector = function(name, desc, choice1, choice2) {
      if (firstAttr) {
        row ++;
        firstAttr = false;
        changesPane.add(new qx.ui.basic.Label(that.tr("Attribute")).set({font: 'bold'}), {row:row, column:0});
        changesPane.add(new qx.ui.basic.Label(that.tr("Local")).set({font: 'bold'}), {row:row, column:1});
        changesPane.add(new qx.ui.basic.Label(that.tr("Server")).set({font: 'bold'}), {row:row, column:2});
      }
      row ++;
      itemId ++;
      layout.setRowFlex(row);

      // Create the toggle fields
      var group = new qx.ui.form.RadioGroup();
      var left = new gosa.ui.container.MergeItem(choice1);
      var right = new gosa.ui.container.MergeItem(choice2);
      items[name] = [left, right];
      group.add(left);
      group.add(right);

      mergeWidgets[name] = {
        local : left,
        remote : right
      };

      // Add the elements to the grid layout
      var translateString = desc;
      if (typeof translateString === "string") {
        translateString = that["tr"](desc);
      }
      changesPane.add(new qx.ui.basic.Label(translateString).set({rich: true, alignY:'middle'}), {row: row, column: 0});  // jshint
      // ignore:line
      changesPane.add(left, {row: row, column: 1});
      changesPane.add(right, {row: row, column: 2});

      // Add a callback for later evaluation.
      selections.push(function(){
        return({name: name, choice: left.getValue() && left.isEnabled()});
      });
    };

    // This method creates an extension merge selector.
    var createExtension = function(name, enabled) {
      var desc = name;

      // Add header
      if (firstExt) {
        row ++;
        layout.setRowHeight(row, 20);
        row ++;
        firstExt = false;
        changesPane.add(new qx.ui.basic.Label(that.tr("Extension")).set({font: 'bold'}), {row:row, column:0});
        changesPane.add(new qx.ui.basic.Label(that.tr("Local")).set({font: 'bold'}), {row:row, column:1});
        changesPane.add(new qx.ui.basic.Label(that.tr("Server")).set({font: 'bold'}), {row:row, column:2});
      }

      // Prepare the layout
      row ++;
      itemId ++;
      layout.setRowFlex(row);

      // Create the selector
      var group = new qx.ui.form.RadioGroup();
      var left = null;
      var right = null;
      if (enabled) {
        left = new gosa.ui.container.MergeItem(new qx.ui.basic.Label("disabled"));
        right = new gosa.ui.container.MergeItem(new qx.ui.basic.Label("enabled"));
      }
      else {
        left = new gosa.ui.container.MergeItem(new qx.ui.basic.Label("enabled"));
        right = new gosa.ui.container.MergeItem(new qx.ui.basic.Label("disabled"));
      }
      left.setAppearance("mergeButton");
      right.setAppearance("mergeButton");
      extList[name] = [left, right];
      group.add(left);
      group.add(right);

      // Add the selectors to the grid
      changesPane.add(new qx.ui.basic.Label(that["tr"](desc)).set({rich: true}), {row: row, column: 0});  // jshint ignore:line
      changesPane.add(left, {row: row, column: 1});
      changesPane.add(right, {row: row, column: 2});
      extensions.push(function() {
        return({name: name, choice: left.getValue() && left.isEnabled()});
      });

      // Act on selection changes of the extension selectors (disable property selectors and those extension that do not
      // fulfil their requirements)
      var func = function() {
        var tmp, state;

        // Disable all extension according to their dependencies
        for (var extName in extDependencies) {
          for (tmp in extDependencies[extName]) {
            if (extDependencies[extName][tmp] === name) {
              if (extName in extList) {
                state = !enabled && left.getValue() || enabled && right.getValue();
                extList[extName][0].setEnabled(state);
                extList[extName][1].setEnabled(state);
              }
            }
          }
        }
      };

      // Disable extension dependent selectors
      left.addListener("changeValue", func, this);
      callOnce.push(func);
    };

    var id;

    // Add extension actions in correct order
    for (id in order) {
      if (qx.lang.Array.contains(exts['removed'], order[id])) {
        createExtension(order[id], false);
      }
    }

    // Add the collected attrs
    mods.forEach(function(item) {
      createSelector(item.attributeName, item.label, item.localWidget, item.remoteWidget);
    });

    this.__handleBlocks(blocks);

    // Ensure that the selectors are valid.
    for (var fid in callOnce) {
      callOnce[fid]();
    }

    // Add Elements into a scroll area
    var ok = gosa.ui.base.Buttons.getOkButton();
    ok.setAppearance("button-primary");
    var scroller = new qx.ui.container.Scroll();
    scroller.add(changesPane);
    this.addElement(new qx.ui.basic.Label(this.tr("The object has been updated while you were modifying it. Please determine to keep your local or the server version of the item. You can achieve this by marking the appropriate one.")).set({rich:true, wrap:true}), {flex:1});
    this.addElement(scroller, {flex:1});
    this.addButton(ok);

    // When OK is pressed then send an event containing the user decissions.
    ok.addListener("execute", function() {
        var res = {};
        var ext = {};
        var item, tmp;

        for (item in selections) {
          tmp = selections[item]();
          res[tmp['name']] = tmp['choice'];
        }
        for (item in extensions) {
          tmp = extensions[item]();
          ext[tmp['name']] = tmp['choice'];
        }
        this.fireDataEvent("merge", {'attributes': res, 'ext' : ext});
        this.close();
      }, this);
  },

  events: {
    "merge" : "qx.event.type.Data"
  },

  members : {

    __mergeWidgets : null,

    /**
     * @param blocks {Object}
     */
    __handleBlocks : function(blocks) {
      qx.core.Assert.assertObject(blocks);

      for (var attributeName in blocks) {
        if (blocks.hasOwnProperty(attributeName)) {
          blocks[attributeName].forEach(qx.lang.Function.curry(this.__bindWidgets, attributeName), this);
        }
      }
    },

    /**
     * @param attributeName {String}
     * @param blockName {String}
     */
    __bindWidgets : function(attributeName, blockName) {
      qx.core.Assert.assertString(attributeName);
      qx.core.Assert.assertString(blockName);

      var map = this.__mergeWidgets;
      if (!map[attributeName] || !map[blockName]) {
        return;
      }
      this.addBidirectionalBinding(map[attributeName].local, "value", map[blockName].local, "value");
      this.addBidirectionalBinding(map[attributeName].remote, "value", map[blockName].remote, "value");
    }
  },

  destruct : function() {
    this.__mergeWidgets = null;
  }
});

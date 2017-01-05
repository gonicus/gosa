/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/*
#asset(gosa/*)
*/
qx.Class.define("gosa.ui.dialogs.MergeDialog", {

  extend: gosa.ui.dialogs.Dialog,

  construct: function(mods, exts, relations, ext_dependencies, order)
  {
    this.base(arguments, this.tr("Merge required"), gosa.Config.getImagePath("status/dialog-information.png", 22));
    this.setResizable(true);
    this.setWidth(800);
    this.setHeight(500);

    var layout = new qx.ui.layout.Grid(15);
    layout.setColumnFlex(1, 1);
    layout.setColumnFlex(2, 2);
    layout.setColumnFlex(3, 2);
    var changesPane = new qx.ui.container.Composite(layout);

    var row = 0;
    var itemid = 0;
    var callonce = [];
    var extlist = {};
    var selections = [];
    var extensions = [];
    var items = {};
    var that = this;
    var firstAttr = true
    var firstExt = true

    // This method adds a new merge-selector for a property.
    var createSelector = function(name, desc, choice1, choice2){
      if(firstAttr){
        row ++;
        layout.setRowHeight(row, 20);
        row ++;
        firstAttr = false;
        changesPane.add(new qx.ui.basic.Label(that.tr("Attribute")).set({font: 'bold'}), {row:row, column:0});
        changesPane.add(new qx.ui.basic.Label(that.tr("Local")).set({font: 'bold'}), {row:row, column:1});
        changesPane.add(new qx.ui.basic.Label(that.tr("Server")).set({font: 'bold'}), {row:row, column:2});
      }
      row ++;
      itemid ++;
      layout.setRowFlex(row);

      // Create the toggle fields
      var group = new qx.ui.form.RadioGroup();
      var left = new gosa.ui.container.MergeItem(choice1);
      var right = new gosa.ui.container.MergeItem(choice2);
      left.setAppearance("mergeButton");
      right.setAppearance("mergeButton");
      items[name] = [left, right];
      group.add(left);
      group.add(right);

      // Add the elements to the grid layout
      changesPane.add(new qx.ui.basic.Label(that["tr"](desc)).set({rich: true}), {row: row, column: 0});  // jshint ignore:line
      changesPane.add(left, {row: row, column: 1});
      changesPane.add(right, {row: row, column: 2});

      // Add a callback for later evaluation.
      selections.push(function(){
        return({name: name, choice: left.getValue() && left.isEnabled()});
      });
    }

    // This method creates an extension merge selector.
    var createExtension = function(name, enabled){
      var desc = name;

      // Add header
      if(firstExt){
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
      itemid ++;
      layout.setRowFlex(row);

      // Create the selector
      var group = new qx.ui.form.RadioGroup();
      var left = null;
      var right = null;
      if(enabled){
        left = new gosa.ui.container.MergeItem(new qx.ui.basic.Label("disabled"));
        right = new gosa.ui.container.MergeItem(new qx.ui.basic.Label("enabled"));
      }else{
        left = new gosa.ui.container.MergeItem(new qx.ui.basic.Label("enabled"));
        right = new gosa.ui.container.MergeItem(new qx.ui.basic.Label("disabled"));
      }
      left.setAppearance("mergeButton");
      right.setAppearance("mergeButton");
      extlist[name] = [left, right];
      group.add(left);
      group.add(right);

      if(relations['buddyTexts'][desc]){
        desc = relations['buddyTexts'][desc];
      }

      // Add the selectors to the grid
      changesPane.add(new qx.ui.basic.Label(that["tr"](desc)).set({rich: true}), {row: row, column: 0});  // jshint ignore:line
      changesPane.add(left, {row: row, column: 1});
      changesPane.add(right, {row: row, column: 2});
      extensions.push(function(){
        return({name: name, choice: left.getValue() && left.isEnabled()});
      });

      // Act on selection changes of the extension selectors
      // (disable property selectors and those extension that do not
      // fullfil their requirements)
      var func = function(e){

        // Disable all extension according to their dependencies
        for(var ename in ext_dependencies){
          for(var tmp in ext_dependencies[ename]){
            if(ext_dependencies[ename][tmp] == name){
              if(ename in extlist){
                var state = !enabled && left.getValue() || enabled && right.getValue();
                extlist[ename][0].setEnabled(state);
                extlist[ename][1].setEnabled(state);
              }
            }
          }
        }

        // Enable/disable property switches
        var state = left.getValue();
        if(enabled){
          state = !state;
        }
        if(relations['widgets'][name]){
          for(var citem in relations['widgets'][name]){
            var tmp = relations['widgets'][name][citem];
            if(relations['bindings'][tmp]){
              var item = relations['bindings'][tmp];
              if(items[item]){
                for(var i in items[item]){
                  items[item][i].setEnabled(state);
                }
              }
            }
          }
        }
      }

      // Disable extension dependen selectors
      left.addListener("changeValue", func, this);
      callonce.push(func);
    }

    // Add extension actions in correct order
    for(var id in order){
      if(qx.lang.Array.contains(exts['added'], order[id])){
        createExtension(order[id], true);
      }
      if(qx.lang.Array.contains(exts['removed'], order[id])){
        createExtension(order[id], false);
      }
    }

    // Add the collected attrs
    for(var id in mods){
      createSelector(mods[id]['name'], mods[id]['desc'], mods[id]['value_1'], mods[id]['value_2']);
    }

    // Ensure that the selectors are valid.
    for(var fid in callonce){
      callonce[fid]();
    }

    // Add Elements into a scroll area
    var ok = gosa.ui.base.Buttons.getOkButton();
    var scroller = new qx.ui.container.Scroll();
    scroller.add(changesPane);
    this.addElement(new qx.ui.basic.Label(this.tr("The object has been updated while you were modifying it. Please determine to keep your local or the server version of the item. You can achieve this by marking the appropriate one.")).set({rich:true, wrap:true}), {flex:1});
    this.addElement(scroller, {flex:1});
    this.addButton(ok);

    // When OK is pressed then send an event containing the user decissions.
    ok.addListener("execute", function(){
        var res = {};
        var ext = {};
        for(var item in selections){
          var tmp = selections[item]();
          res[tmp['name']] = tmp['choice'];
        }
        for(var item in extensions){
          var tmp = extensions[item]();
          ext[tmp['name']] = tmp['choice'];
        }
        this.fireDataEvent("merge", {'attrs': res, 'ext' : ext});
      }, this);
  },

  events: {
    "merge" : "qx.event.type.Data"
  }
});

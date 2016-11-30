/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/* ************************************************************************

#asset(gosa/*)

 ************************************************************************ */

/**
 * This is the main application class of your custom application "gosa"
 */
qx.Class.define("gosa.ui.Renderer",
{
  extend : qx.ui.container.Composite,

  /*
   *****************************************************************************
   MEMBERS
   *****************************************************************************
   */
  construct : function()
  {
    // Call super class
    this.base(arguments);
    this.setLayout(new qx.ui.layout.VBox());

    // Widget store
    this._widgets = {};
    this._extension_to_widgets = {};
    this._translated_extensions = {};

    // Flex map
    this._flexMap = {
      "Fixed": 0,
      "Ignored": 0,
      "Minimum": 0,
      "Maximum": 10,
      "Preferred": 1,
      "Expanding": 4,
      "MinimumExpanding": 2
    };

    // Tabstops, bindings and resources
    this._tabstops = new Array();
    this._current_tabstops = new Array();
    this._bindings = {};
    this._current_bindings = {};
    this._dialogs = {};
    this._buddies = {};
    this._current_buddies = {};
    this._resources = {};
    this._widget_ui_properties = {};

    this._extension_to_page = {};
    this._widget_to_page = {};
    this.__bindings = [];
    this._mapping = gosa.Cache.widget_mapping;
  },

  properties :
  {
    modified : {init: false, check: "Boolean", "apply": "__applyModified"},
    object : {init: null},
    title_: { init: "Unknown", inheritable : true },
    icon_: { init: null, inheritable : true },
    properties_: { init: null, inheritable : true },
    attributeDefinitions_: { init: null, inheritable : true },
    UiDefinition_: { init: null, inheritable : true }
  },

  events: {
    "done": "qx.event.type.Event"
  },

  statics :
  {

    executeAction : function(dialog, target, object, icon)
    {
      if (dialog) {
        object.debug("launch dialog named: gosa.ui.dialogs." + dialog);

        if (gosa.ui.dialogs[dialog]) {
          var dialogW = new gosa.ui.dialogs[dialog](object);
          dialogW.setIcon(icon);
          dialogW.show();
        }
      }

      if (target) {
        var re = /^([^(]+)\((.*)\)$/;
        var info = re.exec(target);
        var method = info[1];
        var params = info[2].split(",");

        var ps = /%\(([^)]+)\)s/;
        for (var i in params) {
          var match = ps.exec(params[i]);
          if (match) {
            var data = object[match[1]];
            if (typeof data === 'string') {
              params[i] = params[i].replace(match[0], data);
            } else {
              params[i] = params[i].replace(match[0], data[0]);
            }
          }
        }

        params.unshift(method, function(result, error) {
          if (error) {
            new gosa.ui.dialogs.Error(error.message).open();
          } else {
            object.debug("call method " + target + " on object returned with: " + result);
          }
        }, this);

        object.callMethod.apply(object, params);
      }
    },

    classes: null,

    /* A static method that returns a gui widget for the given object,
     * including all properties, tabs (extensions).
     * */
    getWidget : function(cb, context, obj)
    {
      // Initialize meta-class cache
      if(!gosa.ui.Renderer.classes){
        gosa.ui.Renderer.classes = {};
      }

      /* Tell the object that it is under control of a gui.
       * */
      obj.setUiBound(true);

      // Check if there's an override for the definitions
      // If not, use the objects gui templates.
      var use_cached = true;
      var ui_definition = gosa.Cache.gui_templates;

      // Create a extension->widgetMapping
      if(!gosa.Cache.widget_mapping){
        var map = {'widgets': {}, 'bindings': {}, 'rbindings': {}, 'types': {}, 'buddyTexts': {}};
        for(var eid in ui_definition){
          for(var tid in ui_definition[eid]){
            map['widgets'][eid] = [];
            var doc = qx.xml.Document.fromString(ui_definition[eid][tid]);
            var widgets = doc.getElementsByTagName("widget");
            for(var wid in widgets){
              var windowTitle = null;
              if(widgets[wid]['attributes']){
                var wname = widgets[wid]['attributes']['name']['value'];
                map['widgets'][eid].push(wname);
                map['types'][wname] = widgets[wid]['attributes']['class']['value'];

                var buddy = null;
                var text = null;
                for(var pid in widgets[wid].childNodes){
                  var p = widgets[wid].childNodes[pid];
                  if(p['attributes'] && p['attributes']['name'] && p['attributes']['name']['value'] == "buddy"){
                    buddy = p.childNodes[1].firstChild.nodeValue;
                  }
                  if(p['attributes'] && p['attributes']['name'] && p['attributes']['name']['value'] == "windowTitle"){
                    windowTitle = p.childNodes[1].firstChild.nodeValue;
                  }
                  if(p['attributes'] && p['attributes']['name'] && p['attributes']['name']['value'] == "text"){
                    try{
                      text = p.childNodes[1].firstChild.nodeValue;
                    }catch(e){
                      text = "";
                    }
                  }
                }
                if(buddy && text){
                  map['buddyTexts'][buddy] = text;
                }
              }
              if(windowTitle && !(map['buddyTexts'][eid])){
                map['buddyTexts'][eid] = windowTitle;
              }
            }
            var connections = doc.getElementsByTagName("connection");
            for(var id in connections){
              var sender, receiver = null;
              for(var cid in connections[id].childNodes){
                if(connections[id].childNodes[cid].nodeName == "sender"){
                  sender = connections[id].childNodes[cid].firstChild.nodeValue;
                }
                if(connections[id].childNodes[cid].nodeName == "slot"){
                  receiver = connections[id].childNodes[cid].firstChild.nodeValue.replace(/^property_/, "");
                  receiver = receiver.replace(/\(\)$/, "");
                }
              }
              if(sender && receiver){
                map['bindings'][sender] = receiver;
                map['rbindings'][receiver] = sender;
              }
            }
          }
        }
        gosa.Cache.widget_mapping = map;
      }

      var clazz;

      // Check if we can use a cached gui here.
      if(use_cached && obj.classname in gosa.ui.Renderer.classes){
        clazz = gosa.ui.Renderer.classes[obj.classname];
      }else{

        // This method returns an apply-method for the given attribute
        // (We unfortunately require it this way, due to reference handling in loops)
        var getApplyMethod = function(name){
          var func = function(value){
            var widgetName = qx.lang.Object.getKeyFromValue(this._bindings, name);
            if (this._widgets[widgetName]) {
              if(!this._widgets[widgetName]._was_initialized || this._object.is_reloading){
                this.setWidgetValue(widgetName, value);
                this._widgets[widgetName]._was_initialized = true;
              }
            }
          };
          return(func);
        };

        // Prepare meta-class properties here.
        var properties = {};
        var members = {};

        // Prepare the property list for the meta-class we are going to create.
        // Add each remote-object-property as qooxdoo-property and add its setter-method too.
        for(var name in obj.attribute_data){
          var upperName = name.charAt(0).toUpperCase() + name.slice(1);
          var applyName = "_apply_" + upperName;
          var prop = {nullable: true, apply: applyName, event: "changed" + upperName};
          members[applyName] = getApplyMethod(name);
          properties[name] = prop;
        }

        // Finaly create the meta-class
        var name = obj.baseType + "Object";
        var def = {extend: gosa.ui.Renderer, properties: properties, members: members};
        clazz = qx.Class.define(name, def);

        // Store generated meta-class in the class-cache to speed up opening the next gui.
        if(use_cached){
          gosa.ui.Renderer.classes[obj.classname] = clazz;
        }
      }

      // Create an instance of the just created meta-class, set attribute-definitions and
      // generate the gui-widget out of the ui_definitions.
      var widget = new clazz();
      widget._object = obj;
      widget.setObject(obj);
      widget.setAttributeDefinitions_(obj.attribute_data);
      widget.setUiDefinition_(ui_definition);
      widget.configure();

      // Connect to the object event 'propertyUpdateOnServer' to be able to act on property changes.
      // e.g. set an invalid-decorator for specific widget.
      var id = obj.addListener("propertyUpdateOnServer", widget.actOnEvents, widget);
      widget.__bindings.push({id: id, widget: obj});
      id = obj.addListener("updatedAttributeValues", widget.actOnEvents, widget);
      widget.__bindings.push({id: id, widget: obj});
      id = obj.addListener("foundDifferencesDuringReload", widget.actOnEvents, widget);
      widget.__bindings.push({id: id, widget: obj});

      // Listen to reconnects to check if the object reference is still available
      id = gosa.io.Sse.getInstance().addListener("changeConnected", function(e) {
        if (e.getData() === true) {
          var rpc = gosa.io.Rpc.getInstance();
          rpc.cA("checkObjectRef", obj.instance_uuid)
          .then(function(result) {
            if (result === false) {
              new gosa.ui.dialogs.Info(this.tr("This object has been closed by the backend!")).open();
              if (this._closingHint) {
                this._closingHint.close();
                this._closingHint = null;
              }
              this.fireEvent("done");
            }
          }, this);
        }
      }, widget);
      widget.__bindings.push({id: id, widget: gosa.io.Sse.getInstance()});

      // Act on remove events
      id = obj.addListener("removed", function(){
          new gosa.ui.dialogs.Info(this.tr("This object does not exist anymore!")).open();
          this.fireEvent("done");
        }, widget);
      widget.__bindings.push({id: id, widget: obj});

      // automatic closing by backend
      id = obj.addListener("closing", function(e) {
        var data = e.getData();
        if (data['uuid'] !== this._object.uuid) {
          // wrong uuid
          return;
        }
        switch (data['state']) {
          case "closing":
            this._closingHint = new gosa.ui.dialogs.ClosingObject(this._object.dn, parseInt(data['minutes'])*60);
            this._closingHint.open();
            this._closingHint.addListener("closeObject", this.__cancel, this);
            this._closingHint.addListener("continue", function() {
              // tell the backend that the user wants to continue to edit the object
              var rpc = gosa.io.Rpc.getInstance();
              if (this._object && !this._object.isDisposed()) {
                rpc.cA("continueObjectEditing", this._object.instance_uuid);
              } else {
                this._closingHint.close();
              }
            }, this);
            break;
          case "closing_aborted":
            this._closingHint.close();
            this._closingHint = null;
            break;
          case "closed":
            this._closingHint.close();
            this._closingHint = null;
            new gosa.ui.dialogs.Info(this.tr("This object has been closed due to inactivity!")).open();
            this.fireEvent("done");
            break;
        }

      }, widget);
      widget.__bindings.push({id: id, widget: obj});

      cb.apply(context, [widget]);
    }
  },

  destruct : function(){

    // Remove all listeners from our object.
    qx.event.Registration.removeAllListeners(this);

    // Try to remove all bindings we've made during gui preparation.
    for(var item in this.__bindings){
      this.__bindings[item]['widget'].removeListenerById(this.__bindings[item]['id']);
    }

    // Reset class members
    this._disposeObjects("__toolMenu", "__okBtn", "__cancelBtn", "_extendButton", "_retractButton", "_actionButton");
    this.__bindings = null;
    this._extension_to_widgets = null;
    this._flexMap = null;
    this._buddies = null;
    this._tabstops = null;
    this._bindings = null;
    this._object = null;
    this._current_buddies = null;
    this._current_tabstops = null;
    this._current_bindings = null;
    this._resources = null;
    this._current_widgets = null;
    this._widgets = null;
    this._object = null;
    this._widgets = null;
    this._tabstops = null;
    this._bindings = null;
    this._resources = null;
    this._current_tabstops = null;
    this._current_buddies = null;
    this._current_bindings = null;
    this._current_widgets = null;
    this._tabContainer = null;
    this._extension_to_widgets = null;
    this._widget_to_page = null;
    this._widget_ui_properties = null;
    this._extension_to_page = null;
    this._translated_extensions = null;
    this._buttonPane = null;
  },

  members :
  {
    _object: null,
    _widgets: null,
    _tabstops: null,
    _bindings: null,
    _resources: null,
    _mapping: null,
    _current_tabstops: null,
    _current_buddies: null,
    _current_bindings: null,
    _current_widgets: null,
    _tabContainer: null,
    _extension_to_widgets: null,
    _widget_to_page: null,
    _widget_ui_properties: null,
    __bindings: null,
    _extension_to_page: null,
    _translated_extensions: null,

    __okBtn: null,
    __cancelBtn: null,
    __toolMenu: null,
    _buttonPane: null,

    /* Establish bindings between object-properties and master-widget input fields.
     * */
    processBindings: function(bindings){

      for(var widgetName in bindings){

        var propertyName = bindings[widgetName];

        // We do not have such a widget!
        if(!(widgetName in this._widgets)){
          this.error("*** found binding info for '"+widgetName+"' but no such widget was created! ***");
          continue;
        }
        this.__bindHelper(this._widgets[widgetName], propertyName, widgetName);
      }
    },


    __bindHelper: function(widget, name, widgetName){
      var id = widget.addListener("changeValue", function(e){
        this.set(name, e.getData());
        this.setModified(true);
      }, this);

      this.__bindings.push({id: id, widget: widget});

      if(!(qx.lang.Array.contains(this._object.attributes, name))){
        this.error("*** found binding info for property '"+name+"' but there is no such property! ***");
      }else{
        this._object.bind(name, this, name);
        this.bind(name, this._object, name);
      }

      for(var item in this._bindings){
        if(this._bindings[item] == name && item != widgetName){
          widget.bind("value", this._widgets[item], "value");
          this.bind(name, widget, "value");
        }
      }
    },


    /* Applies the given buddies the labels
     * */
    processBuddies: function(buddies)
    {
      for (var buddy in buddies) {

        // Set buddy
        if(this._widgets[buddy]){
          this._widgets[buddies[buddy]].setBuddy(this._widgets[buddy]);

          if(this._widgets[buddy].hasState("gosaWidget")){
            this._widgets[buddy].setBuddyOf(this._widgets[buddies[buddy]]);
          }

          // Process mandatory flag and inform label about it
          this._widgets[buddies[buddy]].setMandatory(this._widgets[buddy].getMandatory());

          // Add Command if configured
          var command = this._widgets[buddies[buddy]].getCommand();
          if (command) {
            //TODO: collect for dispose
            var hotkey = new qx.ui.command.Command("Ctrl+" + command);
            var id = hotkey.addListener("execute", this._widgets[buddy].shortcutExecute, this._widgets[buddy]);

            this.__bindings.push({id: id, widget: hotkey});
          }
        }
      }
    },

    /* Applies the given tabstops to the gui widgets
     * */
    processTabStops: function(tabstops, page)
    {
      page.addListener("appear", function(){

          for(var i=0; i<tabstops.length; i++){
            var w = this._widgets[tabstops[i]];
            if(w.getReadOnly() || w.isBlocked() || !(w.isEnabled())){
              continue;
            }

            // Safari needs the timeout
            // iOS and Firefox need it called immediately
            // to be on the save side we do both
            setTimeout(function() {
              w.focus();
            });
            w.focus();
            break;
          }
        }, this);


      for (var i= 0; i< tabstops.length; i++) {
        var w = tabstops[i];
        if (this._widgets[w]) {
          this._widgets[w].setTabStopIndex((i + 1) * 20);
        }
      }
    },

    /* This method acts on events send by the remote-object which was used to create this gui-widget.
     * */
    actOnEvents: function(e){
      switch(e.getType()){

        /* Act on 'updatedAttributeValues' events, they tell us, that the backend has
         * updates for drop-down lists etc.
         */
        case "updatedAttributeValues": {
          this.getAttributeDefinitions_()[e.getData()['item']]['values'] = e.getData()['values'];
          var name = qx.lang.Object.getKeyFromValue(this._bindings, e.getData()['item']);
          if(name && this._widgets[name]){
            this._widgets[name].setValues(e.getData()['values']);
          }
        }; break;

        /* If the object was modified somewhere else while we were editing it, we have to
         * show a merge dialog to the user, so that he can decide which changes should take
         * effect.
         * */
        case "foundDifferencesDuringReload": {
          var data = e.getData();
          var mods = [];

          // Collect all attribute changes and prepare the merge-widgets
          for(var name in data['attributes']['changed']){
            var widgetName = this._mapping['rbindings'][name];
            if(widgetName){
              var defs = this.getAttributeDefinitions_()[name];
              var my_value = this._widgets[widgetName].getValue().copy();
              var real_value = data['attributes']['changed'][name];
              if(!this._widgets[widgetName].isMultivalue()){
                real_value = new qx.data.Array([real_value]);
              }else{
                real_value = new qx.data.Array(real_value);
              }
              var classname = this._mapping['types'][widgetName] + "Widget";
              if(gosa.ui.widgets[classname]){
                if(gosa.ui.widgets[classname].getMergeWidget){
                  var w1 = gosa.ui.widgets[classname].getMergeWidget(my_value);
                  var w2 = gosa.ui.widgets[classname].getMergeWidget(real_value);
                  var desc = name;
                  if(widgetName in this._mapping['buddyTexts']){
                    desc = this._mapping['buddyTexts'][widgetName]
                  }
                  mods.push({name: name, value_1: w1, value_2: w2, desc: desc});
                }else{
                  this.error("Missing getMergeWidget for " + classname);
                }
              }
            }
          }

          // Collect all added attributes and prepare the merge-widgets
          for(var name in data['attributes']['added']){
            var widgetName = this._mapping['rbindings'][name];
            if(widgetName){
              var defs = this.getAttributeDefinitions_()[name];
              var real_value = data['attributes']['added'][name];
              if(!defs['multivalue']){
                real_value = new qx.data.Array([real_value]);
              }else{
                real_value = new qx.data.Array(real_value);
              }
              var classname = this._mapping['types'][widgetName] + "Widget";
              if(gosa.ui.widgets[classname]){
                if(gosa.ui.widgets[classname].getMergeWidget){
                  var w1 = new qx.ui.basic.Label("<i>" + this.tr("empty") + "<i>").set({rich: true});
                  var w2 = gosa.ui.widgets[classname].getMergeWidget(real_value);
                  var desc = name;
                  if(widgetName in this._mapping['buddyTexts']){
                    desc = this._mapping['buddyTexts'][widgetName]
                  }
                  mods.push({name: name, value_1: w1, value_2: w2, desc: desc});
                }else{
                  this.error("Missing getMergeWidget for " + classname);
                }
              }
            }
          }

          // Collect all removed attributes and prepare the merge-widgets
          for(var id in data['attributes']['removed']){
            var name = data['attributes']['removed'][id];
            var widgetName = this._mapping['rbindings'][name];
            if(widgetName){
              var my_value = this._widgets[widgetName].getValue().copy();
              var classname = this._mapping['types'][widgetName] + "Widget";
              if(gosa.ui.widgets[classname]){
                if(gosa.ui.widgets[classname].getMergeWidget){
                  var w1 = gosa.ui.widgets[classname].getMergeWidget(my_value);
                  var w2 = new qx.ui.basic.Label("<i>" + this.tr("removed") + "<i>").set({rich: true});
                  var desc = name;
                  if(widgetName in this._mapping['buddyTexts']){
                    desc = this._mapping['buddyTexts'][widgetName]
                  }
                  mods.push({name: name, value_1: w1, value_2: w2, desc: desc});
                }else{
                  this.error("Missing getMergeWidget for " + classname);
                }
              }
            }
          }

          // No changes detected
          if(!mods.length){
            this._object.reload(function(result, error){
              this.info("Object was reloaded, but no merge was required!");
            }, this);
            return;
          }

          // Create a list containing all extensions in correct order,
          // to allow retraction or extending without dependency problems.
          var order = [];
          var that = this;
          var resolveDep = function(name){
            if(that._object.extensionDeps[name].length){
              for(var item in that._object.extensionDeps[name]){
                resolveDep(that._object.extensionDeps[name][item]);
              }
            }
            if(!qx.lang.Array.contains(order, name)){
              order.push(name);
            }
          }
          for(var item in this._object.extensionDeps){
            resolveDep(item);
          }

          /* Open the merge dialog to allow the user to select which changes he wants to take over.
           * */
          var dialog = new gosa.ui.dialogs.MergeDialog(mods, data['extensions'], this._mapping, this._object.extensionDeps, order);
          dialog.open();
          dialog.center();
          dialog.addListener("merge", function(e){

            // Disable the dialog while merging
            dialog.setEnabled(false);

            // Create a dict containing all property values we have to update.
            // (Update means alls property values that differ from the current server state)
            var keep = {};
            var res = e.getData();
            for (var name in res['attrs']) {
              if (res['attrs'][name]) {
                var widgetName = this._mapping['rbindings'][name];

                // If there is no widget with the given name, then we
                // just have to set an empty value for the property.
                if (this._widgets[widgetName]) {
                  keep[name] = this._widgets[widgetName].getValue().copy();
                }
                else {
                  keep[name] = new qx.data.Array();
                }
              }
            }

            // Reload the object (Opens a new object on the server side).
            this._object.reload(function() {
              // Get extension details from the server.
              return this._object.get_extension_types();
            }, this)
            .then(function(result) {
              // Create a queue which later extends or retracts
              // addons step by step.
              // Without queue, we cannot handle multiple retractions or extensions
              // due to the fact all they would be executed all once.
              // --
              // Once the Queue has finished it updates the widget values (see variable 'keep').
              var updated = 0;
              var queue = [];
              var that = this;
              var handleQueue = function() {
                if (queue.length) {
                  var f = queue.pop();
                  f();
                }
                else {

                  // Update widget values
                  for (var name in keep) {
                    var widgetName = that._mapping['rbindings'][name];
                    if (that._widgets[widgetName]) {
                      that._widgets[widgetName].setValue(keep[name]);
                      that._widgets[widgetName].setModified(true);
                      that._widgets[widgetName].enforceUpdateOnServer();
                    }
                  }

                  // Reload the "values"-list for dropdown-boxes, selectboxes etc.
                  if (updated) {
                    that._object.refreshAttributeInformation(null, null, true);
                  }

                  dialog.close();
                }
              }

              // Check which extensions have to be added and removed.
              // (Compares current extension state with server state)
              var to_extend = [];
              var to_retract = [];
              for (var ext in result) {

                // Active on server but not in client.
                if (result[ext] && !this._extension_to_page[ext]) {

                  // Create the tab according to backend status
                  this._createTabsForExtension(ext);
                  updated++;

                  // We do not want to take over the backend status
                  // -> retract the extension again
                  if (res['ext'][ext]) {
                    to_retract.push(ext);
                  }
                }
                else if (!result[ext] && this._extension_to_page[ext]) {

                  // Remove the tab according to backend status
                  this._removeTabsForExtension(ext);

                  // We do not want to take over the backend status
                  // -> extend the extension again
                  if (res['ext'][ext]) {
                    to_extend.push(ext);
                  }
                }
              }

              // Create a list containing all extensions in correct order,
              // to allow retraction or extending without dependency problems.
              var order = [];
              var that = this;
              var resolveDep = function(name) {
                if (that._object.extensionDeps[name].length) {
                  for (var item in that._object.extensionDeps[name]) {
                    var tmp = that._object.extensionDeps[name][item];
                    if (qx.lang.Array.contains(to_retract, tmp) && that._extension_to_page[name]) {
                      to_retract.push(name);
                    }
                    resolveDep(tmp);
                  }
                }
                if (!qx.lang.Array.contains(order, name)) {
                  order.push(name);
                }
              }
              for (var item in this._object.extensionDeps) {
                resolveDep(item);
              }

              // Helper method which inserts a 'retraction' to the queue.
              var del = function(ext) {
                queue.push(function() {
                  that._retractObjectFrom(ext, handleQueue);
                });
              }

              // Helper method which inserts a 'extension' to the queue.
              var add = function(ext) {
                queue.push(function() {
                  that._extendObjectWith(ext, handleQueue);
                });
              }

              // Add the missing extensions to the queue.
              order = order.reverse();
              for (var item in order) {
                if (qx.lang.Array.contains(to_extend, order[item])) {
                  add(order[item]);
                }
              }

              // Add the missing retractions to the queue.
              order = order.reverse();
              for (var item in order) {
                if (qx.lang.Array.contains(to_retract, order[item])) {
                  del(order[item]);
                }
              }

              // Process the queue
              handleQueue();
            }, this);
            }, this);
        }; break;

        /* This event tells us that a property-change on the server-side has finished.
         * Now check its result and set decorator for the widgets accordingly.
         * */
        case "propertyUpdateOnServer": {
            var data = e.getData();
            var name = data['property'];
            this.resetError(name);
            if(!data['success']){
              if(name in this._widget_to_page){
                this._tabContainer.setSelection([this._widget_to_page[name]]);
                this.setError(name, data['error']);
              }else{
                new gosa.ui.dialogs.Error(data['error'].message).open();
              }
            }
          }; break;
      }
    },


    /* Extract resources from the given ui-defintion
     * */
    extractResources : function(ui_def)
    {
      var res = {};

      // Find resources (e.g. image-paths) before we do anything more
      for (var i=0; i<ui_def.length; i++) {
        for (var r=0; r<ui_def[i].childNodes.length; r++) {
          if (ui_def[i].childNodes[r].nodeName == "resources") {
            var resources = ui_def[i].childNodes[r];
            for (var j=0; j<resources.childNodes.length; j++) {
              var topic = resources.childNodes[j];
              if (topic.nodeName != "resource") {
                continue;
              }
              var files = {};
              for (var f in topic.childNodes) {
                var item = topic.childNodes[f];
                if (item.nodeName == "file") {
                  files[":/" + item.firstChild.nodeValue] = gosa.Config.spath + "/resources/" + item.firstChild.nodeValue;
                }
              }
              qx.lang.Object.mergeWith(res, files);
            }
          }
        }
      }

      return res;
    },


    /* Configure this widget for the given ui_defintion.
     * The ui_definition is parsed and qooxdoo-objects are created for
     * each found xml-tag.
     * */
    configure : function()
    {
      var okButton = gosa.ui.base.Buttons.getOkButton();
      this.__okBtn = okButton;
      this.__okBtn.setEnabled(false);
      this.__okBtn.setTabIndex(30000);

      // If there are extensions or more than one gui-page
      // available for this object, then put all pages into a tab-page.
      var container;
      var ui_definition = this.getUiDefinition_();
      this._tabContainer = container = new gosa.ui.tabview.TabView();
      this._tabContainer.getChildControl("bar").setScrollStep(150);
      this.add(container, {flex: 1});

      // Create a list of tab-names and order them
      var exten_list = new Array(this._object.baseType);
      var tmp = Object.keys(this._object.extensionTypes);
      tmp.sort();
      exten_list = exten_list.concat(tmp);

      // Walk through each tab
      for (var ext_key in exten_list) {
        var extension = exten_list[ext_key];

        // Skip empty definitions or disabled ones.
        if (!ui_definition[extension] ||
            (!this._object.extensionTypes[extension] && extension != this._object.baseType)) {
          continue;
        }
        this._createTabsForExtension(extension);
      }

      // Prepare tool menu
      this.__toolMenu = new qx.ui.menu.Menu();
      this._updateToolMenu();

      container.getChildControl("bar").setMenu(this.__toolMenu);

      // Add button static button line for the moment
      var paneLayout = new qx.ui.layout.HBox().set({
        spacing: 4,
        alignX : "right",
        alignY : "middle"
      });
      var buttonPane = this._buttonPane = new qx.ui.container.Composite(paneLayout).set({
        marginTop: 11
      });

      okButton.addState("default");
      buttonPane.add(okButton);
      okButton.addListener("click", function() {

        // Close all sub-dialogs
        for(var d in this._dialogs){
          this._dialogs[d].close();
        }

        // Ensure that all widgets are in a valid state before starting the
        // save action on the server.
        for(var item in this._widgets){
          if(this._widgets[item].hasState('gosaInput') && !this._widgets[item].isValid()){
            if(this._widgets[item].getAttribute() in this._widget_to_page){
              this._tabContainer.setSelection([this._widget_to_page[this._widgets[item].getAttribute()]]);
            }
            return;
          }
        }

        this._object.commit(function(result, error){
          if(error){
            if(error.topic && error.topic in this._widget_to_page){
              this._object.fireDataEvent("propertyUpdateOnServer", {success: !error, error: error, property: error.topic});
            }else{
              this.error(error);
              this.error(error.message);
              this.error(error.topic);
              this.error(error.code);
              this.error(error.details);
              new gosa.ui.dialogs.Error(error.message).open();
            }
          }else{
            this._object.close(function(result, error){
              if(error){
                new gosa.ui.dialogs.Error(error.message).open();
              }else{
                this.fireEvent("done");
              }
            }, this);
          }
        }, this);
      }, this);

      var cancelButton = gosa.ui.base.Buttons.getCancelButton();
      this.__cancelBtn = cancelButton;
      this.__cancelBtn.setTabIndex(30001);
      buttonPane.add(cancelButton);

      cancelButton.addListener("click", this.__cancel, this);

      this.add(buttonPane);

      return true;
    },

    __cancel: function() {
      // Close all sub-dialogs
      for(var d in this._dialogs){
        this._dialogs[d].close();
      }
      if (this._object) {
        this._object.close(function(result, error) {
          if (error) {
            new gosa.ui.dialogs.Error(error.message).open();
          }
        }, this);
      }
      this.fireEvent("done");
    },


    /* Adds a listener to the given widgets to enable/disable
     * it depending on the given blockedBy definition.
     * */
    _processBlockedBy: function(widget, data){

      // Skip if there is no block info
      if(!data.length){
        return;
      }

      /* This method get called to verfiy if the widget
       * has to be blocked or not.
       * */
      var that = this;
      var func = function(data, widget){
          var block = false;
          for(var k=0; k<data.length; k++){
            var propertyName = data[k]['name'];
            var value = data[k]['value'];
            var values = that._object.get(propertyName).toArray();
            for(var i=0; i< values.length; i++){
              if(value == values[i]){
                block = true;
              }
            }
          }
          if(block){
            widget.block();
          }else{
            widget.unblock();
          }
        };

      /* Extract information about when to block the widget
       * and add a listener to the source-widget, to check
       * its values again after they were modified.
       * */
      for(var k=0; k<data.length; k++){
        var propertyName = data[k]['name'];
        var name = qx.lang.Object.getKeyFromValue(this._bindings, propertyName);

        if(this._widgets[name]){
          var id = this._widgets[name].addListener("changeValue", function(e){
            func(data, widget);
          }, this);
          this.__bindings.push({id: id, widget: this._widgets[name]});
        }else{
          this.error("invalid blocking information for '" + propertyName + "' there is no such widget!");
        }

        // Initially check blocking
        func(data, widget);
      }
    },


    _makeExtensionMenuEntry : function(ext, props, resources) {
      var eb = new qx.ui.menu.Button(this['tr'](this.getStringProperty('windowTitle', props)),
        this.getIconProperty('windowIcon', props, resources));
      var id = eb.addListener("execute", function() {
        this.extendObjectWith(ext);
      }, this);

      this.__bindings.push({id: id, widget: eb});

      return eb;
    },

    _makeRetractMenuEntry : function(ext, props, resources) {
      var eb = new qx.ui.menu.Button(this['tr'](this.getStringProperty('windowTitle', props)),
        this.getIconProperty('windowIcon', props, resources));
      var id = eb.addListener("execute", function() {
        this.retractObjectFrom(ext);
      }, this);

      this.__bindings.push({id: id, widget: eb});
      return eb;
    },

    _makeActionMenuEntry : function(node, resources)
    {
      var widget = node.childNodes;
      var props = {};

      for (var i in widget) {
        if (widget[i].nodeName == "property") {
          var tmp = this.processProperty(widget[i]);
          for (var item in tmp) {
            props[item] = tmp[item];
          }
        }
      }

      var label = this['tr'](this.getStringProperty("text", props));
      var icon = this.getIconProperty("icon", props, resources);
      var dialog = this.getStringProperty("dialog", props);
      var target = this.getStringProperty("target", props);
      var shortcut = this.getStringProperty("shortcut", props);
      var condition = this.getStringProperty("condition", props);

      var name = null;
      for (var a = 0; a < node.attributes.length; a++) {
        if(node.attributes[a].nodeName == "name"){
          name = node.attributes[a].nodeValue;
          break;
        }
      }

      // Check if we need to add a global shortcut
      if (shortcut) {
        //TODO: collect for dispose
        var hotkey = new qx.ui.command.Command(shortcut);
        var id = hotkey.addListener("execute", function() {gosa.ui.Renderer.executeAction(dialog, target, this._object, icon);}, this);
        this.__bindings.push({id: id, widget: hotkey});
      }

      // Evaluate enabled state
      var enabled = undefined;
      var eb = new qx.ui.menu.Button(label, icon);
      eb.setAppearance("icon-menu-button");

      /* Calculate action dependencies. Right now we support attribute and
       * method dependent checks in the ui-template file:
       *  <string notr="true">!isLocked</string>
       *  <string notr="true">accountUnlockable(dn)</string>
       * */
      if (condition) {
        var stateR = /^(!)?([^(]*)(\((.*)\))?$/;
        var state = stateR.exec(condition);

        // Method based condition?
        if (state[4] != undefined){
          var method = state[2];

          // Collect arguments that have to be passed to the method call.
          var attrs = state[4].split(",");
          var args = [];

          for(var item in attrs) {
        	  var value;
            if(attrs[item] == "dn" || attrs[item] == "uuid"){
              value = this._object[attrs[item]];
            }else{
              try{
                value = this._object.get(attrs[item]).toArray();
              }catch(e){
                if(attrs[item][0] == "\"" || attrs[item][0] == "'"){
                  value = [attrs[item].replace(/^["']/, "").replace(/["']$/, "")];
                }
              }
              if(value.length){
                value = value[0];
              }else{
                value = null;
              }
            }
            args.push(value);
          }
          args.unshift(method);

          // Now execute the method with its arguments and set the button state
          eb.setEnabled(false);
          eb.addListener("appear", function() {
            var rpc = gosa.io.Rpc.getInstance();
            rpc.cA.apply(rpc, args)
            .then(function(result) {
              result = (state[1] == "!") ? !result : result;
              eb.setEnabled(result);
            }).catch(function(error) {
              new gosa.ui.dialogs.Error(error).open();
              eb.setEnabled(false);
            });
          });
        } else {

          // Calculate attribute based condition
          var attribute = state[2];
          var value = this._object.get(attribute).toArray();
          if(value.length){
            value = value[0];
          }else{
            value = false;
          }
          if (state[1] == "!") {
            enabled = !(value === true);
          } else {
            enabled = value === true;
          }
        }
      }

      if (enabled != undefined) {
        eb.setEnabled(enabled);
      }
      var id = eb.addListener("execute", function() {
        gosa.ui.Renderer.executeAction(dialog, target, this._object, icon);
      }, this);
      this.__bindings.push({id: id, widget: eb});
      return({'item': eb, 'name': name});
    },

    /* Walk through extension ui-definitions and return all tab titles
     * */
    getTranslatedExtension : function(ext)
    {
      if (!this._translated_extensions[ext]) {
        this._translated_extensions[ext] = [];
        for(var ui in gosa.Cache.gui_templates[ext]){
          var nodes = qx.xml.Document.fromString(gosa.Cache.gui_templates[ext][ui]);
          var widget = nodes.firstChild.getElementsByTagName("widget").item(0).childNodes;
          this._translated_extensions[ext].push(this.getStringProperty("windowTitle", this.extractProperties(widget)));
        }
      }
      return this._translated_extensions[ext];
    },

    /* Make the tool menu reflect the current object/extension settings.
     * */
    _updateToolMenu : function()
    {
      if (this._extendButton && this.__toolMenu.indexOf(this._extendButton) != -1) {
        this.__toolMenu.remove(this._extendButton);
      }

      if (this._retractButton && this.__toolMenu.indexOf(this._retractButton) != -1) {
        this.__toolMenu.remove(this._retractButton);
      }

      if (this._actionButton && this.__toolMenu.indexOf(this._actionButton) != -1) {
        this.__toolMenu.remove(this._actionButton);
      }

      // Find base level actions
      var actions_to_add = {};
      var actionMenu = new qx.ui.menu.Menu();
      var ui_s = gosa.Cache.gui_templates[this._object.baseType];
      for (var i=0; i<ui_s.length; i++) {
        var nodes = qx.xml.Document.fromString(ui_s[i]);
        var actions = nodes.firstChild.getElementsByTagName("action");
        for (var i=0; i<actions.length; i++) {
          var entry = this._makeActionMenuEntry(actions[i]);
          actions_to_add[entry['name']] = entry['item'];
        }
      }

      var extendMenu = new qx.ui.menu.Menu();
      var retractMenu = new qx.ui.menu.Menu();

      for (var ext in this._object.extensionTypes) {
        if (gosa.Cache.gui_templates[ext] && gosa.Cache.gui_templates[ext].length != 0) {

          // Find first widget definition and extract windowIcon and windowTitle
          var ui_s = gosa.Cache.gui_templates[ext];
          var added = false;
          for (var i=0; i<ui_s.length; i++) {
            var nodes = qx.xml.Document.fromString(ui_s[i]);
            var resources = this.extractResources(nodes.childNodes);
            var widget = nodes.firstChild.getElementsByTagName("widget").item(0).childNodes;
            var props = this.extractProperties(widget);

            if (this._object.extensionTypes[ext]) {
              if (!added) {
                retractMenu.add(this._makeRetractMenuEntry(ext, props, resources));
                added = true;
              }

              // Find extension level actions
              var actions = nodes.firstChild.getElementsByTagName("action");
              for (var j=0; j<actions.length; j++) {
                var entry = this._makeActionMenuEntry(actions[j], resources);
                actions_to_add[entry['name']] = entry['item'];
              }

            } else {
              if (!added) {
                extendMenu.add(this._makeExtensionMenuEntry(ext, props, resources));
                added = true;
              }
            }
          }
        }
      }

      var sorted = [];
      for(var key in actions_to_add) {
        sorted[sorted.length] = key;
      }
      sorted.sort();

      for(var aitem in sorted){
        actionMenu.add(actions_to_add[sorted[aitem]]);
      }

      if (extendMenu.hasChildren()) {
        this._extendButton = new qx.ui.menu.Button(this.tr("Extend"), "@FontAwesome/f0fe", null, extendMenu);
        this._extendButton.setAppearance("icon-menu-button");
        this.__toolMenu.add(this._extendButton);
      }

      if (retractMenu.hasChildren()) {
        this._retractButton = new qx.ui.menu.Button(this.tr("Retract"), "@FontAwesome/f146", null, retractMenu);
        this._retractButton.setAppearance("icon-menu-button");
        this.__toolMenu.add(this._retractButton);
      }

      if (actionMenu.hasChildren()) {
        this._actionButton = new qx.ui.menu.Button(this.tr("Action"), "@FontAwesome/f0d0", null, actionMenu);
        this._actionButton.setAppearance("icon-menu-button");
        this.__toolMenu.add(this._actionButton);
      }

      if (this.__toolMenu.hasChildren()) {
        this.__toolMenu.setEnabled(true);
      } else {
        this.__toolMenu.setEnabled(false);
      }
    },

    /* Extract widget properties as a hash
     * */
    extractProperties : function(widget)
    {
      var props = {};

      for (var i in widget) {
        if (widget[i].nodeName == "property") {
          var tmp = this.processProperty(widget[i]);
          for (var item in tmp) {
            props[item] = tmp[item];
          }
        }
      }

      return props;
    },

    _retractObjectFrom : function(extension, callback)
    {
      this._object.retract(function(result, error) {
        if (error) {
          new gosa.ui.dialogs.Error(qx.lang.String.format(this.tr("Failed to retract the %1 extension: %2"), [extension, error.message])).open();
          this.error(error.message);
        } else {

          this._removeTabsForExtension(extension);
          this._object.refreshMetaInformation(this._updateToolMenu, this);
          this.setModified(true);

          if (callback) {
            callback();
          }
        }
      }, this, extension);
    },

    _removeTabsForExtension: function(extension){
      var pages = this._extension_to_page[extension];
      for (var i = 0; i<pages.length; i++) {
        pages[i].fireEvent("close");
        pages[i].dispose();
      }
      delete this._extension_to_page[extension];

      // Remove all widget references and then close the page
      for(var widget in this._extension_to_widgets[extension]){
        widget = this._extension_to_widgets[extension][widget];
        delete this._widgets[widget];

        if(this._widget_to_page[this._bindings[widget]]){
          delete(this._widget_to_page[this._bindings[widget]]);
        }
      }
      delete this._extension_to_widgets[extension];
    },

    /* Retract extension
     * */
    retractObjectFrom : function(extension)
    {
      // Check for dependencies, eventually ask for additional extensions
      var dependencies = [];

      for (var ext in this._object.extensionDeps) {
        if (this._object.extensionDeps[ext].indexOf(extension) != -1) {
          dependencies.push(ext);
        }
      }

      if (dependencies) {

        // Strip already used deps
        var needed = [];
        for (var dep in dependencies) {
          var ext = dependencies[dep];
          if (this._object.extensionTypes[ext] && gosa.Cache.gui_templates[ext] && gosa.Cache.gui_templates[ext].length != 0) {
            needed.push(ext);
          }
        }

        // Ask user to enable the remaining dependencies
        if (needed.length != 0) {
          var dlg = new gosa.ui.dialogs.Dialog(this.trn("Dependent extension", "Dependent extensions", needed.length),
                  gosa.Config.getImagePath("status/dialog-warning.png", 22));
          dlg.setWidth(400);

          var lst = "<ul>";
          var len = 0;
          for (var i = 0; i<needed.length; i++) {
            var items = this.getTranslatedExtension(needed[i]);
            len += items.length;
            for(var item=0; item<items.length;item++ ){
              lst += "<li><b>" + items[item] + "</b></li>";
            }
          }
          lst += "</ul>";

          var message = new qx.ui.basic.Label(
            this.trn("To retract the <b>%1</b> extension from this object, the following additional extension needs to be removed: %2",
                     "To retract the <b>%1</b> extension from this object, the following additional extensions need to be removed: %2",
                     len, this.getTranslatedExtension(extension).join(', '), lst) +
            this.trn("Do you want the dependent extension to be removed?", "Do you want the dependent extensions to be removed?", needed.length)
          );
          message.setRich(true);
          message.setWrap(true);

          dlg.addElement(message);

          var ok = gosa.ui.base.Buttons.getOkButton();
          ok.addListener("execute", function() {
            var queue = [];
            for (var i = 0; i<needed.length; i++) {
              queue.push([this._retractObjectFrom, this, [needed[i]]]);
            }

            queue.push([this._retractObjectFrom, this, [extension]]);
            gosa.Tools.serialize(queue);

            dlg.close();
          }, this);

          dlg.addButton(ok);
          var cancel = gosa.ui.base.Buttons.getCancelButton();
          cancel.addListener("execute", dlg.close, dlg);
          dlg.addButton(cancel);

          dlg.show();

          return;
        }
      }

      // Remove tab
      this._retractObjectFrom(extension);
    },


    /* Extend the current object with the given extension
     * and then reload its values and extension states.
     * Afterwards - create the visual part of the tabs.
     * */
    _extendObjectWith : function(extension, callback) {
      this._object.extend(extension)
      .then(function() {
        return this._object.refreshMetaInformation(extension);
      }, this)
      .then(function() {
        this._updateToolMenu();
        return this._object.refreshAttributeInformation();
      }, this)
      .then(function() {
        this._createTabsForExtension(extension);
        if (callback) {
          callback();
        }
        this.setModified(true);
      }, this)
      .catch(function(error) {
        this.error(error.message);
      }, this);
    },

    /* Extend the object with the given extension
     * */
    extendObjectWith : function(type)
    {
      // Check for dependencies, eventually ask for additional extensions
      var dependencies = this._object.extensionDeps[type];
      if (dependencies) {

        // Strip already used deps
        var needed = [];
        for (var dep in dependencies) {
          if (!this._object.extensionTypes[dependencies[dep]]) {
            needed.push(dependencies[dep]);
          }
        }

        // Ask user to enable the remaining dependencies
        if (needed.length != 0) {
          var dlg = new gosa.ui.dialogs.Dialog(this.trn("Missing extension", "Missing extensions", needed.length),
                  gosa.Config.getImagePath("status/dialog-warning.png", 22));
          dlg.setWidth(400);

          // Collect a list of all items that have to be extended too
          var lst = "<ul>";
          var len = 0;
          for (var i = 0; i<needed.length; i++) {
            var items = this.getTranslatedExtension(needed[i]);
            len += items.length;
            for(var item=0; item<items.length;item++ ){
              lst += "<li><b>" + items[item] + "</b></li>";
            }
          }
          lst += "</ul>";

          // Create the message for the dialog
          var message = new qx.ui.basic.Label(
            this.trn("To extend the object by the <b>%1</b> extension, the following additional extension is required: %2",
                     "To extend the object by the <b>%1</b> extension, the following additional extensions are required: %2",
                     len, this.getTranslatedExtension(type).join(', '), lst) +
            this.trn("Do you want the missing extension to be added?", "Do you want the missing extensions to be added?", needed.length)
          );
          message.setRich(true);
          message.setWrap(true);

          dlg.addElement(message);

          var ok = gosa.ui.base.Buttons.getOkButton();
          ok.addListener("execute", function() {
            var queue = [];

            // Setup additional tab(s)
            for (var i = 0; i<needed.length; i++) {
              queue.push([this._extendObjectWith, this, [needed[i]]]);
            }

            // Setup desired tab
            queue.push([this._extendObjectWith, this, [type]]);
            gosa.Tools.serialize(queue);

            dlg.close();
          }, this);
          dlg.addButton(ok);
          var cancel = gosa.ui.base.Buttons.getCancelButton();
          cancel.addListener("execute", dlg.close, dlg);
          dlg.addButton(cancel);

          dlg.show();
          return;
        }
      }

      // Setup new tab
      this._extendObjectWith(type);
    },


     /* Some tabs/extensions may provide sub-dialog to edit additional properties.
      * This method creates these dialogs and stores an instance of each dialog to
      * be able to pop them up on demand.
      * */
    createDialog: function(extension){

      // Use dialog ui definitions
      var ui_definition = gosa.Cache.gui_dialogs;

      // We may have multiple dialogs per extension
      for (var tab=0; tab<ui_definition[extension].length; tab++) {

        // Extract the gui information
        var info = this.__createTabContent(extension, qx.xml.Document.fromString(ui_definition[extension][tab]).childNodes, true);
        try{
          var dialogName = info['properties']['dialogName']['string'];
        }catch(e){
          dialogName = "unknown";
          this.error("the dialog no. "+tab+" of extension "+extension+" has no 'dialogName' attribute!");
        }

        try{
          var dialogTitle = info['properties']['windowTitle']['string'];
        }catch(e){
          dialogTitle = "unknown";
          this.error("the dialog no. "+tab+" of extension "+extension+" has no 'dialogTitle' attribute!");
        }

        // Create a new dialog and add the created gui-widget to it.
        var dialog = new qx.ui.window.Window(dialogTitle);
        dialog.setLayout(new qx.ui.layout.VBox(10));
        dialog.add(info['widget'], {flex: 1});
        dialog.addListener("appear", dialog.center, dialog);

        // Keep track of extension pages.
        this._extension_to_page[extension].push(info['page']);

        // Add a close button to the dialog
        var l = new qx.ui.layout.HBox();
        l.setAlignX("right");
        var c = new qx.ui.container.Composite(l);
        var b = gosa.ui.base.Buttons.getButton(qx.locale.Manager.tr("OK"), "actions/dialog-ok.png");
        c.add(b);
        b.addListener("execute", dialog.close, dialog);
        dialog.add(c);

        // Store the dialog
        this._dialogs[dialogName] = dialog;
      }
    },


    /* The method creates the content for tabs and DIALOGs.
     * All widgets are created, buddies linked, properties set, bindings established, all
     * you need to use the gui is done within here.
     *
     * This method returns an info object containing multiple information about the gui page created
     * and additional properties.
     * */
    __createTabContent: function(extension, ui_def, is_dialog){

      // Clean-up values that were collected per-loop.
      this._current_widgets = [];
      this._current_bindings = {};
      this._current_tabstops = new Array();
      this._current_buddies = {};

      // Parse the ui definition of the object
      var resources = this.extractResources(ui_def);
      for (var attr in resources) {
        this._resources[attr] = resources[attr];
      }

      // Create the gui-part for this tab
      if(!this._extension_to_widgets){
        this._extension_to_widgets = {};
      }

      var info = this.processUI(extension, ui_def);
      if (info) {

        // Take over properties of base type
        if (this._object.baseType == extension || extension == "ContainerObject") {
          this.setProperties_(info['properties']);
        }

        // Create a new tab-page with the generated gui as content.
        var title = info['widget'].title_;
        var icon = info['widget'].icon_;
        if(!title){
          title = "Unknown";
        }
        if(!icon){
          icon = null;
        }
        var page = new qx.ui.tabview.Page(this['tr'](title), icon);
        page.setLayout(new qx.ui.layout.VBox());
        page.add(info['widget'], {flex:1});
        info['page'] = page;

        this._extension_to_page[extension].push(page);

        // Add "remove extension" buttons to all non-base tabs.
        if (extension != this._object.baseType) {
          page.setShowCloseButton(true);
          page.setUserData("type", extension);

          var closeButton = page.getButton();
          closeButton.getChildControl("close-button").setToolTip(new qx.ui.tooltip.ToolTip(this.tr("Remove extension")));
          closeButton.removeListener("close", page._onButtonClose, page);
          var id = closeButton.addListener("close", function() {
            this.retractObjectFrom(page.getUserData("type"));
          }, this);
          this.__bindings.push({id: id, widget: closeButton});
        }

        // Transmit object property definitions to the widgets
        for(var item in this._current_widgets){
          this.processWidgetProperties(this._current_widgets[item]);
        }

        this.processBuddies(this._current_buddies);
        this.processBindings(this._current_bindings);

        // Create a mapping from widget to page
        for(item in this._current_widgets){
          var widgetName = this._current_bindings[this._current_widgets[item]];

          if(!is_dialog){
            this._widget_to_page[widgetName] = page;
          }

          // Toggler
          var attrs_defs = this.getAttributeDefinitions_()[widgetName];
          if(attrs_defs && Object.keys((attrs_defs['blocked_by']).length > 0)){
            this._processBlockedBy(this._widgets[this._current_widgets[item]], attrs_defs['blocked_by']);
          }
        }

        // Connect this master-widget with the object properties, establish tabstops
        this.processTabStops(this._current_tabstops, page);

        for(item in this._current_widgets){
          if(this._widgets[this._current_widgets[item]].hasState("gosaInput")){
            this._widgets[this._current_widgets[item]].setInitComplete(true);
          }
        }

      } else {
        this.info("*** no widget found for '" + extension + "'");
      }
      return(info);
    },


    /* Create the gui elements for the given extension
     * and appends a new page the tab-container.
     * */
    _createTabsForExtension: function(extension){
      this._extension_to_page[extension] = [];
      this.createDialog(extension);

      // Process each tab of the current extension
      var ui_definition = this.getUiDefinition_();
      for (var tab=0, l=ui_definition[extension].length; tab<l; tab++) {
        var info = this.__createTabContent(extension, qx.xml.Document.fromString(ui_definition[extension][tab]).childNodes, false);
        this._tabContainer.add(info['page'], {flex: 1});
      }
    },


    /* Transfer collected widget-properties to the widgets.
      */
    processWidgetProperties: function(item){
      var w = this._widgets[item];
      var widgetName = this._bindings[item];
      var defs = this.getAttributeDefinitions_()[widgetName];

      if(w && w.hasState("gosaWidget")){
        if(defs){
          w.setAttribute(widgetName);
          for(var extension in this._extension_to_widgets){
            if(qx.lang.Array.contains(this._extension_to_widgets[extension], item)){
              w.setExtension(extension);
              break;
            }
          }
          w.setCaseSensitive(defs['case_sensitive']);
          w.setBlockedBy(defs['blocked_by']);
          w.setDefaultValue(defs['default']);
          w.setDependsOn(defs['depends_on']);
          w.setMandatory(defs['mandatory']);
          w.setMultivalue(defs['multivalue']);
          w.setReadOnly(defs['readonly']);
          w.setType(defs['type']);
          w.setUnique(defs['unique']);
          w.setValues(defs['values']);

          if(this._buddies[item] && this._widgets[this._buddies[item]]){
            w.setLabelText(this._widgets[this._buddies[item]].getText());
          }
        }
        w.setGuiProperties(this._widget_ui_properties[item]);
      }
    },


    /**
     * This method contains the initial application code and gets called
     * during startup of the application
     *
     * @lint ignoreDeprecated(alert)
     */

    processUI : function(loc, nodes)
    {
      // Process one level, watch out for nodes we know
      for (var i=0; i<nodes.length; i++) {
        var node = nodes[i];

        // Skip non elements
        if (node.nodeType !== 1) {
          continue;
        }

        // Top level UI element
        if (node.nodeName == "ui") {
          if (node.getAttribute("version") !== "4.0") {
            this.error("*** UI format 4.0 is needed to continue processing!");
            return null;
          }

          // Continue with processing the child nodes
          return this.processElements(loc, node.childNodes);

        } else {
          this.error("*** unexpected element '" + node.nodeName + "'");
        }
      }

      return null;
    },

    processElements : function(loc, nodes)
    {
      var widgets = new Array();

      // Process one level, watch out for nodes we know
      for (var i=0; i<nodes.length; i++) {
        var node = nodes[i];

        // Skip non elements
        if (node.nodeType !== 1) {
          continue;
        }

        // Class
        if (node.nodeName == "class") {
          this.name = node.firstChild.nodeValue;
          this.debug("setting widget name to '" + this.name + "'");

        // Widget
        } else if (node.nodeName == "widget") {
          var widget = this.processWidget(loc, node);
          if(!widget){
            this.error("Skipped widget creation!");
          }else{
            widgets.push(widget);
          }

        // Spacer
        } else if (node.nodeName == "spacer") {
          widgets.push(this.processSpacer(node));

        // Layout
        } else if (node.nodeName == "layout") {
          var layout_name = node.getAttribute("name");
          var layout_type = node.getAttribute("class");
          var widget = null;
          var properties = {};

          this.debug("layout '" + layout_name + "' (" + layout_type + ")");

          if (layout_type == "QGridLayout") {
            var layout = new qx.ui.layout.Grid();
            widget = new qx.ui.container.Composite(layout);

          } else if (layout_type == "QFormLayout") {
            var layout = new qx.ui.layout.Grid();
            layout.setColumnFlex(1, 1);
            widget = new qx.ui.container.Composite(layout);

          } else if (layout_type == "QHBoxLayout") {
            var layout = new qx.ui.layout.HBox(5);
            widget = new qx.ui.container.Composite(layout);

          } else if (layout_type == "QVBoxLayout") {
            var layout = new qx.ui.layout.VBox(5);
            widget = new qx.ui.container.Composite(layout);

          } else {
            this.error("*** unknown layout type '" + layout_type + "' in processElements()!");
            continue;
          }
          widget.setAllowGrowX(false);
          widget.setAllowGrowY(false);

          // Inspect layout items
          for (var j=0; j<node.childNodes.length; j++) {

            var topic = node.childNodes[j];
            if (topic.nodeType == 1 && topic.nodeName == "item") {

              if (layout_type == "QGridLayout") {
                var column = parseInt(topic.getAttribute("column"));
                var row = parseInt(topic.getAttribute("row"));
                var colspan = parseInt(topic.getAttribute("colspan"));
                var rowspan = parseInt(topic.getAttribute("rowspan"));
                var wdgt = this.processElements(loc, topic.childNodes);
                var pos = {row: row, column: column};
                if (colspan) {
                  pos['colSpan'] = colspan;
                }
                if (rowspan) {
                  pos['rowSpan'] = rowspan;
                }
                widget.add(wdgt['widget'], pos);
                widget.getLayout().setColumnFlex(column, this.extractHFlex(wdgt['properties']));
                widget.getLayout().setRowFlex(row, this.extractVFlex(wdgt['properties']));
                if(this.extractVFlex(wdgt['properties'])){
                  widget.setAllowGrowY(true);
                }
                if(this.extractHFlex(wdgt['properties'])){
                  widget.setAllowGrowX(true);
                }

              } else if (layout_type == "QFormLayout") {
                var column = parseInt(topic.getAttribute("column"));
                var row = parseInt(topic.getAttribute("row"));
                var colspan = parseInt(topic.getAttribute("colspan"));
                var rowspan = parseInt(topic.getAttribute("rowspan"));

                var pos = {row: row, column: column};
                if (colspan) {
                  pos['colSpan'] = colspan;
                }
                if (rowspan) {
                  pos['rowSpan'] = rowspan;
                }

                var wdgt = this.processElements(loc, topic.childNodes);
                widget.add(wdgt['widget'], pos);
                widget.getLayout().setColumnFlex(column, this.extractHFlex(wdgt['properties'], 1));
                widget.getLayout().setRowFlex(row, this.extractVFlex(wdgt['properties'], 1));

                if(this.extractVFlex(wdgt['properties'])){
                  widget.setAllowGrowY(true);
                }
                if(this.extractHFlex(wdgt['properties'])){
                  widget.setAllowGrowX(true);
                }

              } else if (layout_type == "QHBoxLayout") {
                var wdgt = this.processElements(loc, topic.childNodes);
                widget.add(wdgt['widget'], {flex: this.extractHFlex(wdgt['properties'])});
                if(this.extractHFlex(wdgt['properties'])){
                  widget.setAllowGrowX(true);
                }
                if(this.extractVFlex(wdgt['properties'])){
                  widget.setAllowGrowY(true);
                }
              } else if (layout_type == "QVBoxLayout") {
                var wdgt = this.processElements(loc, topic.childNodes);
                widget.add(wdgt['widget'], {flex: this.extractVFlex(wdgt['properties'])});
                if(this.extractHFlex(wdgt['properties'])){
                  widget.setAllowGrowX(true);
                }
                if(this.extractVFlex(wdgt['properties'])){
                  widget.setAllowGrowY(true);
                }
              }

            }

            if (topic.nodeType == 1 && topic.nodeName == "property") {
              var tmp = this.processProperty(topic);
              for (var item in tmp) {
                properties[item] = tmp[item];
              }
            }

            var layout = widget.getLayout();

            if (layout_type == "QGridLayout") {
              layout.setSpacing(5);

            } else if (layout_type == "QFormLayout") {
              var hs = 3;
              var vs = 3;

              if (properties['labelAlignment']) {
                var align = this.getSetProperty('labelAlignment', properties);
                var h = "center";
                var v = "middle";

                if (align.indexOf("Qt::AlignLeft") != -1) {
                  h = "left";
                }
                if (align.indexOf("Qt::AlignRight") != -1) {
                  h = "right";
                }
                if (align.indexOf("Qt::AlignTop") != -1) {
                  v = "top";
                }
                if (align.indexOf("Qt::AlignBottom") != -1) {
                  v = "bottom";
                }

                layout.setColumnAlign(0, h, v);
              } else {
                layout.setColumnAlign(0, "right", "top");
              }

              if (properties['horizontalSpacing']) {
                hs = this.getNumberProperty('horizontalSpacing', properties);
                if (hs < 0) {
                  hs = 3;
                }
              }

              if (properties['verticalSpacing']) {
                vs = this.getNumberProperty('verticalSpacing', properties);
                if (vs < 0) {
                  vs = 3;
                }
              }

              layout.setSpacingX(3 + hs);
              layout.setSpacingY(3 + vs);
            }
          }

          widgets.push({widget: widget, properties: properties});

        // Collect tabstops
        } else if (node.nodeName == "tabstops") {

          for (var j=0; j<node.childNodes.length; j++) {

            var topic = node.childNodes[j];
            if (topic.nodeType == 1 && topic.nodeName == "tabstop") {
              this._tabstops.push(topic.firstChild.nodeValue);
              this._current_tabstops.push(topic.firstChild.nodeValue);
            }
          }

        // Collect bindings
        } else if (node.nodeName == "connections") {

          for (var j=0; j<node.childNodes.length; j++) {
            var topic = node.childNodes[j];
            if (topic.nodeType != 1) {
              continue;
            }

            var sender = null;
            var slot = null;

            for (var k=0; k<topic.childNodes.length; k++) {
              if (topic.childNodes[k].nodeName == "sender") {
                sender = topic.childNodes[k].firstChild.nodeValue;
              }
              if (topic.childNodes[k].nodeName == "slot") {
                slot = topic.childNodes[k].firstChild.nodeValue;
              }
            }
            this._bindings[sender] = slot.slice(9, slot.length - 2);
            this._current_bindings[sender] = slot.slice(9, slot.length - 2);

          }

        // Ignore resources - they're already processed
        } else if (node.nodeName == "resources") {

        } else if (node.nodeName == "action") {

        } else {
          this.error("*** unexpected element '" + node.nodeName + "'");
        }

      }

      // If there is more than one widget on this level,
      // automatically return a canvas layout with these widgets.
      if (widgets.length == 1) {
        if (widgets[0]) {
          return widgets[0];
        } else {
          return null;
        }
      } else {
        this.info("*** migrate your GUI to use layouts instead of plain widget collections");

        var base = new qx.ui.container.Composite(new qx.ui.layout.Canvas());

        for (var i in widgets) {
          if (widgets[i]){
            // Set geometry
            var x = 0;
            var y = 0;
            var geometry = this.getGeometryProperty('geometry', widgets[i]['properties']);
            if (geometry) {
              x = geometry['x'];
              y = geometry['y'];
            }
            base.add(widgets[i]['widget'], {left: x, top: y});
          }
        }

        return {widget: base, properties: {}};
      }
    },

    processSpacer : function(node)
    {
      var w = new qx.ui.core.Widget();

      // Evaluate properties
      var properties = {};
      for (var i= 0; i<node.childNodes.length; i++) {
        var n = node.childNodes[i];
        if (n.nodeName == "property") {
          var tmp = this.processProperty(n);

          for (var item in tmp) {
            properties[item] = tmp[item];
          }
        }
      }

      // Handle size hint
      var sizeHint = this.getSizeProperty('sizeHint', properties);
      var sw = 1;
      var sh = 1;
      if (sizeHint) {
        sw = sizeHint['width'];
        sh = sizeHint['height'];
      }
      w.setWidth(sw);
      w.setHeight(sh);

      return {widget: w, properties: properties};
    },

    processWidget : function(loc, node)
    {
      var widgets = new Array();
      var nodes = node.childNodes;

      // Extract general widget information
      var name = node.getAttribute("name");
      var clazz = node.getAttribute("class");
      var properties = {};
      var layout = null;
      var widget = null;

      this.debug("processing widget " + name);

      // Process one level, watch out for nodes we know
      for (var i=0; i<nodes.length; i++) {
        var n = nodes[i];

        // Skip non elements
        if (n.nodeType !== 1) {
          continue;
        }

        // Properties
        if (n.nodeName == "property") {
          var tmp = this.processProperty(n);
          for (var item in tmp) {
            properties[item] = tmp[item];
          }
        }else if (n.nodeName == "column") {
          if(!("columns" in properties)){
            properties['columns'] = {};
          }
          for (var e = 0; e<n.childNodes.length; e++) {
            var item = n.childNodes[e];
            if (item.nodeName == "property") {
              var c_data = this.processProperty(item);
              properties['columns'][c_data['text']['_comment']] = c_data['text']['string'];
            }
          }
        } else if (n.nodeName == "widget") {

          widget = this.processWidget(loc, n);
          if(!widget){
            this.error("Skipped widget creation!");
          }else{
            widgets.push(widget);
          }

          // Layout
        } else if (n.nodeName == "layout") {
          layout = n;

          // Actions are used somewhere else
        } else if (n.nodeName == "action") {

        } else {
          this.error("*** unknown element '" + n.nodeName + "'");
        }
      }

      // Call process*Widget method
      var classname = clazz + "Widget";
      var method = "process" + classname;
      if (gosa.ui.widgets[classname]) {
        widget = new gosa.ui.widgets[classname];
        widget.setParent(this);
        this._widgets[name] = widget;
        widget.setWidgetName(name);
        this.__add_widget_to_extension(name, loc);
        this.processCommonProperties(name, widget, properties);

        // Store widget ui-properties for this widget to be able
        // to process them later.
        this._widget_ui_properties[name] = properties;
      } else if (method in this) {
        widget = this[method](loc, name, properties);
      }else{
        this.error("*** widget '" + classname + "' does not exist!");
        return null;
      }

      // Process one level, watch out for nodes we know
      if (layout != null) {
        var layout_name = layout.getAttribute("name");
        var layout_type = layout.getAttribute("class");

        this.debug("layout '" + layout_name + "' (" + layout_type + ")");

        if (layout_type == "QGridLayout") {
          widget.setLayout(new qx.ui.layout.Grid());

        } else if (layout_type == "QFormLayout") {
          widget.setLayout(new qx.ui.layout.Grid());

        } else if (layout_type == "QHBoxLayout") {
          widget.setLayout(new qx.ui.layout.HBox(5));

        } else if (layout_type == "QVBoxLayout") {
          widget.setLayout(new qx.ui.layout.VBox(5));

        } else {
          this.log("*** unknown layout type '" + layout_type + "' in processWidget()!");
          return null;
        }

        // Inspect layout items
        for (var j=0; j<layout.childNodes.length; j++) {

          var topic = layout.childNodes[j];
          if (topic.nodeType == 1 && topic.nodeName == "item") {

            if (layout_type == "QGridLayout") {
              var column = parseInt(topic.getAttribute("column"));
              var row = parseInt(topic.getAttribute("row"));
              var colspan = parseInt(topic.getAttribute("colspan"));
              var rowspan = parseInt(topic.getAttribute("rowspan"));
              var pos = {row: row, column: column};
              if (colspan) {
                pos['colSpan'] = colspan;
              }
              if (rowspan) {
                pos['rowSpan'] = rowspan;
              }
              var wdgt = this.processElements(loc, topic.childNodes);
              widget.add(wdgt['widget'], pos);
              widget.getLayout().setColumnFlex(column, this.extractHFlex(wdgt['properties']));
              widget.getLayout().setRowFlex(row, this.extractVFlex(wdgt['properties']));

            } else if (layout_type == "QFormLayout") {
              var colspan = parseInt(topic.getAttribute("colspan"));
              var rowspan = parseInt(topic.getAttribute("rowspan"));
              var pos = {};
              if (colspan) {
                pos['colSpan'] = colspan;
              }
              if (rowspan) {
                pos['rowSpan'] = rowspan;
              }
              var wdgt = this.processElements(loc, topic.childNodes);
              widget.add(wdgt['widget'], pos);

            } else if (layout_type == "QHBoxLayout") {
              var wdgt = this.processElements(loc, topic.childNodes);
              widget.add(wdgt['widget'], {flex: this.extractHFlex(wdgt['properties'])});

            } else if (layout_type == "QVBoxLayout") {
              var wdgt = this.processElements(loc, topic.childNodes);
              widget.add(wdgt['widget'], {flex: this.extractVFlex(wdgt['properties'])});
            }
          }
        }
      }

      widgets.push({widget: widget, properties: properties});

      // If there is more than one widget on this level,
      // automatically return a canvas layout with these widgets.
      if (widgets.length == 1) {
        if (widgets[0]['widget']) {
          return widgets[0];
        } else {
          return null;
        }
      } else {
        this.info("*** migrate your GUI to use layouts instead of plain widget collections");

        var base = new qx.ui.container.Composite(new qx.ui.layout.Canvas());

        for (var i in widgets) {
          if (widgets[i]){
            // Set geometry
            var x = 0;
            var y = 0;
            var geometry = this.getGeometryProperty('geometry', widgets[i]['properties']);
            if (geometry) {
              x = geometry['x'];
              y = geometry['y'];
            }
            base.add(widgets[i]['widget'], {left: x, top: y});
          }
        }

        return {widget: base, properties: {}};
      }
    },

    processProperty : function(node)
    {
      var res = {};

      // Transform XML tree to hash
      for (var i = 0; i<node.childNodes.length; i++) {
        if (node.childNodes[i].nodeType === 1) {
          var topic = node.childNodes[i];
          var tmp = {};

          // Move attributes
          for (var a = 0; a < topic.attributes.length; a++) {
            tmp["_" + topic.attributes[a].nodeName] = topic.attributes[a].nodeValue;
          }

          if (node.nodeName == "property") {
            if (topic.childNodes && topic.childNodes.length != 1) {
              tmp[topic.nodeName] = this.processProperty(topic);
            } else {
              tmp[topic.nodeName] = topic.firstChild.nodeValue;
            }

            res[node.getAttribute('name')] = tmp;
          } else {
            if (topic.childNodes && topic.childNodes.length != 1) {
              res[topic.nodeName] = this.processProperty(topic);
            } else {
              res[topic.nodeName] = topic.firstChild.nodeValue;
            }
          }
        }
      }

      return res;
    },

    __add_widget_to_extension : function(name, loc)
    {
      if (!this._extension_to_widgets[loc]) {
        this._extension_to_widgets[loc] = [];
      }
      this._extension_to_widgets[loc].push(name);
      this._current_widgets.push(name);
    },

    processQWidgetWidget : function(loc, name, props)
    {
      var widget = new qx.ui.container.Composite();
      widget.title_ = this.getStringProperty('windowTitle', props);
      widget.icon_ = this.getIconProperty('windowIcon', props);
      this.processCommonProperties(name, widget, props);
      this._widgets[name] = widget;
      this.__add_widget_to_extension(name, loc);
      return widget;
    },

    processQGroupBoxWidget : function(loc, name, props)
    {
      var title = this.getStringProperty('title', props);
      //TODO: create a group box with icons
      var widget = new gosa.ui.widgets.GroupBox(this['tr'](title));
      this.processCommonProperties(name, widget, props);
      this._widgets[name] = widget;
      this.__add_widget_to_extension(name, loc);

      return widget;
    },

    processQScrollAreaWidget : function(loc, name, props)
    {
      var widget = new gosa.ui.widgets.ScrollArea();
      this.processCommonProperties(name, widget, props);
      this._widgets[name] = widget;
      this.__add_widget_to_extension(name, loc);

      return widget;
    },

    processCommonProperties : function(name, widget, props)
    {
      // Set geometry - temporarily disabled
      var geometry = this.getGeometryProperty('geometry', props);
      if (geometry) {
        widget.setWidth(geometry['width']);
        widget.setHeight(geometry['height']);
      }

      // Set tooltip
      var tooltip = this.getStringProperty('toolTip', props);
      if (tooltip != null) {
        widget.setToolTip(new qx.ui.tooltip.ToolTip(this['tr'](tooltip)));
      }

      // Set ro mode
      var readonly = this.getBoolProperty('readOnly', props);
      if (readonly === null) {
        readonly = false;
      }
      var enabled = this.getBoolProperty('enabled', props);
      if (enabled === null) {
        enabled = true;
      }
      if(widget.setReadOnly && (readonly || !enabled)){
        widget.setReadOnly(true);
      }

      // Set maximum size
      var size = this.getSizeProperty('maximumSize', props);
      if (size != null) {
        widget.setMaxWidth(size['width']);
        widget.setMaxHeight(size['height']);
      }

      // Set minimum size
      var size = this.getSizeProperty('minimumSize', props);
      if (size != null) {
        widget.setMinWidth(size['width']);
        widget.setMinHeight(size['height']);
      }

      // Process buddies
      var buddy = this.getCStringProperty('buddy', props);
      if (buddy != null) {
        this._buddies[buddy] = name;
        this._current_buddies[buddy] = name;
      }
    },

    setWidgetValue : function(name, value) {
      this._widgets[name].setValue(value.copy());
    },

    setError : function(name, message)
    {
      var widgetName = qx.lang.Object.getKeyFromValue(this._bindings, name);
      if (this._widgets[widgetName]) {
        this._widgets[widgetName].setError(message);
      } else {
        this.error("*** cannot set invalid message for non existing widget '" + name + "'!");
      }
    },

    resetError : function(name)
    {
      var widgetName = qx.lang.Object.getKeyFromValue(this._bindings, name);
      if (this._widgets[widgetName]) {
        this._widgets[widgetName].resetErrorMessage();
      } else {
        this.error("*** cannot set invalid message for non existing widget '" + name + "'!");
      }
    },

    setWidgetRequired: function(name, flag)
    {
      var widgetName = qx.lang.Object.getKeyFromValue(this._bindings, name);
      if (this._widgets[widgetName]) {
        this._widgets[widgetName].setRequired(flag);
      } else {
        this.error("*** cannot set required flag for non existing widget '" + name + "'!");
      }
    },

    getIconProperty : function(what, props, resources)
    {
      if (!resources) {
        resources = this._resources;
      }

      if (props[what] && props[what]['iconset']['normaloff']) {
        if (props[what]['iconset']['normaloff'].startsWith("@")) {
          return props[what]['iconset']['normaloff'];
        }
        else if (resources[props[what]['iconset']['normaloff']]) {
          return resources[props[what]['iconset']['normaloff']];
        }
      }

      return null;
    },

    getStringProperty : function(what, props)
    {
      if (props[what] && props[what]['string']) {
        return props[what]['string'];
      }

      return null;
    },

    getCStringProperty : function(what, props)
    {
      if (props[what] && props[what]['cstring']) {
        return props[what]['cstring'];
      }

      return null;
    },

    getBoolProperty : function(what, props)
    {
      if (props[what] && props[what]['bool']) {
        return props[what]['bool'] == "true";
      }

      return null;
    },

    getSizeProperty : function(what, props)
    {
      if (props[what] && props[what]['size']) {
        return {'height': parseInt(props[what]['size']['height']), 'width': parseInt(props[what]['size']['width'])};
      }

      return null;
    },

    getSizePolicyProperty : function(what, props)
    {
      if (props[what] && props[what]['sizepolicy']) {
        return {'horstretch': parseInt(props[what]['sizepolicy']['horstretch']), 'verstretch': parseInt(props[what]['sizepolicy']['verstretch'])};
      }

      return null;
     },

    getGeometryProperty : function(what, props)
    {
      if (props[what] && props[what]['rect']) {
        return {
          'x': parseInt(props[what]['rect']['x']),
          'y': parseInt(props[what]['rect']['y']),
          'height': parseInt(props[what]['rect']['height']),
          'width': parseInt(props[what]['rect']['width'])};
      }

      return null;
    },

    getNumberProperty : function(what, props)
    {
      if (props[what] && props[what]['number']) {
        return parseInt(props[what]['number']);
      }

      return null;
    },

    getSetProperty : function(what, props)
    {
      if (props[what] && props[what]['set']) {
        return props[what]['set'].split("|");
      }
      return null;
    },

    getEnumProperty : function(what, props)
    {
      if (props[what] && props[what]['enum']) {
        return props[what]['enum'];
      }
      return null;
    },

    extractHFlex : function(props, dflt)
    {
      if (!dflt) {
        dflt = 1;
      }

      // Take a look at the size type
      var sizeType = this.getEnumProperty("sizeType", props);
      if (sizeType) {
        dflt = this._flexMap[sizeType.replace(/QSizePolicy::/, "")];
      }

      // Take a look at the sizePolicy
      var sizePolicy = this.getSizePolicyProperty("sizePolicy", props);
      if (sizePolicy) {
        dflt = sizePolicy['horstretch'];
      }

      return dflt;
    },

    extractVFlex : function(props, dflt)
    {
      if (!dflt) {
        dflt = 1;
      }

      // Take a look at the size type
      var sizeType = this.getEnumProperty("sizeType", props);
      if (sizeType) {
        dflt = this._flexMap[sizeType.replace(/QSizePolicy::/, "")];
      }

      // Take a look at the sizePolicy
      var sizePolicy = this.getSizePolicyProperty("sizePolicy", props);
      if (sizePolicy) {
        dflt = sizePolicy['verstretch'];
      }

      return dflt;
    },

    /* Applies the modified state for this widget
     * */
    __applyModified: function(value){
      this.debug("modified: ", value);
      this.__okBtn.setEnabled(true);
    }
  }
});

// vim:tabstop=2:expandtab:shiftwidth=2

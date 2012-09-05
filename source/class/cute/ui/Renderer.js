/* ************************************************************************

   Copyright: Cajus Pollmeier <pollmeier@gonicus.de>

   License:

   Authors:

 ************************************************************************ */

/* ************************************************************************

#asset(cute/*)

 ************************************************************************ */

/**
 * This is the main application class of your custom application "cute"
 */
qx.Class.define("cute.ui.Renderer",
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
    this._buddies = {};
    this._current_buddies = {};
    this._resources = {};
    this._widget_ui_properties = {};

    this._extension_to_page = {};
    this._widget_to_page = {};
  },

  properties :
  {
    modified : {init: false, check: "Boolean", "apply": "__applyModified"},
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

    classes: null,

    /* A static method that returns a gui widget for the given object,
     * including all properties, tabs (extensions).
     * */
    getWidget : function(cb, context, obj)
    {
      // Initialize meta-class cache
      if(!cute.ui.Renderer.classes){
        cute.ui.Renderer.classes = {};
      }

      // Check if there's an override for the definitions
      // If not, use the objects gui templates.
      var use_cached = true;
      var ui_definition = obj.templates;

      var clazz;
      
      // Check if we can use a cached gui here.
      if(use_cached && obj.classname in cute.ui.Renderer.classes){
        clazz = cute.ui.Renderer.classes[obj.classname];
      }else{

        // This method returns an apply-method for the given attribute
        // (We unfortunately require it this way, due to reference handling in loops)
        var getApplyMethod = function(name){
          var func = function(value){
            var widgetName = qx.lang.Object.getKeyFromValue(this._bindings, name);
            if (this._widgets[widgetName]) {
              if(!this._widgets[widgetName]._was_initialized){
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
        var def = {extend: cute.ui.Renderer, properties: properties, members: members};
        clazz = qx.Class.define(name, def);

        // Store generated meta-class in the class-cache to speed up opening the next gui.
        if(use_cached){
          cute.ui.Renderer.classes[obj.classname] = clazz;
        }
      }

      // Create an instance of the just created meta-class, set attribute-definitions and
      // generate the gui-widget out of the ui_definitions.
      var widget = new clazz();
      widget._object = obj;
      widget.setAttributeDefinitions_(obj.attribute_data);
      widget.setUiDefinition_(ui_definition);
      widget.configure();

      // Connect to the object event 'propertyUpdateOnServer' to be able to act on property changes.
      // e.g. set an invalid-decorator for specific widget.
      obj.addListener("propertyUpdateOnServer", widget.actOnEvents, widget);

      cb.apply(context, [widget]);
    }
  },

  destruct : function(){
    this._extension_to_widgets = this._flexMap = null;
    this._buddies = this._tabstops = this._bindings = this._object = null;
    this._current_buddies = this._current_tabstops = this._current_bindings = null;
    this._resources = null;
    this._disposeObjects("__okBtn", "__cancelBtn");
    this._disposeMap("_widgets");
  },

  members :
  {
    _object: null,
    _widgets: null,
    _tabstops: null,
    _bindings: null,
    _resources: null,
    _current_tabstops: null,
    _current_buddies: null,
    _current_bindings: null,
    _current_widgets: null,
    _tabContainer: null,
    _extension_to_widgets: null,
    _widget_to_page: null,
    _widget_ui_properties: null,

    __okBtn: null,
    __cancelBtn: null,
    __toolMenu: null,


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
        this.__bindHelper(this._widgets[widgetName], propertyName);
      }
    },


    __bindHelper: function(widget, name){
      widget.addListener("changeValue", function(e){
        this.set(name, e.getData());
        this.setModified(true);
      }, this);

      if(!(qx.lang.Array.contains(this._object.attributes, name))){
        this.error("*** found binding info for property '"+name+"' but there is no such property! ***");
      }else{
        this._object.bind(name, this, name);
        this.bind(name, this._object, name);
      }
    },


    /* Applies the given buddies the labels
     * */
    processBuddies: function(buddies)
    {
      for (var buddy in buddies) {

        // Set buddy
        this._widgets[buddies[buddy]].setBuddy(this._widgets[buddy]);

        if(this._widgets[buddy].hasState("cuteWidget")){
          this._widgets[buddy].setBuddyOf(this._widgets[buddies[buddy]]);
        }

        // Process mandatory flag and inform label about it
        this._widgets[buddies[buddy]].setMandatory(this._widgets[buddy].getMandatory());

        // Add Command if configured
        var command = this._widgets[buddies[buddy]].getCommand();
        if (command) {
          //TODO: collect for dispose
          var hotkey = new qx.ui.core.Command("Ctrl+" + command);
          hotkey.addListener("execute", this._widgets[buddy].shortcutExecute, this._widgets[buddy]);
        }
      }
    },

    /* Applies the given tabstops to the gui widgets
     * */
    processTabStops: function(tabstops)
    {
      for (var i= 0; i< tabstops.length; i++) {
        var w = tabstops[i];
        if (i == 0) {

          // Safari needs the timeout
          // iOS and Firefox need it called immediately
          // to be on the save side we do both
          var _self = this;
          var q = w;
          setTimeout(function() {
            _self._widgets[q].focus();
          });

          this._widgets[w].focus();
        }
        if (this._widgets[w]) {
          this._widgets[w].setTabIndex(i + 1);
        }
      }
    },

    /* This method acts on events send by the remote-object which was used to create this gui-widget.
     * */
    actOnEvents: function(e){
      switch(e.getType()){

        /* This event tells us that a property-change on the server-side has finished.
         * Now check its result and set decorator for the widgets accordingly.
         * */
        case "propertyUpdateOnServer": {

            var data = e.getData();
            var name = data['property'];
            if(name in this._widget_to_page){
              this._tabContainer.setSelection([this._widget_to_page[name]]);
            }
            if(data['success']){
              this.resetWidgetInvalidMessage(name);
              this.setWidgetValid(name, true);
            }else{
              this.setWidgetInvalidMessage(name, data['error']['message']);
              this.setWidgetValid(name, false);
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
      for (var q=0; q<ui_def.length; q++) {
        for (var r=0; r<ui_def[q].childNodes.length; r++) {
          if (ui_def[q].childNodes[r].nodeName == "resources") {
            var resources = ui_def[q].childNodes[r];
            for (var j=0; j<resources.childNodes.length; j++) {
              var topic = resources.childNodes[j];
              if (topic.nodeName != "resource") {
                continue;
              }
              var files = {};
              for (var f in topic.childNodes) {
                var item = topic.childNodes[f];
                if (item.nodeName == "file") {
                  files[":/" + item.firstChild.nodeValue] = cute.Config.spath + "/" + cute.Config.getTheme() + "/resources/" + item.firstChild.nodeValue;
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
     * The ui_definition is parsed and qooxdoo-object are created for
     * each found xml-tag.
     * */
    configure : function()
    {

      // If there are extensions or more than one gui-page 
      // available for this object, then put all pages into a tab-page.
      var container;
      var ui_definition = this.getUiDefinition_();
      this._tabContainer = container = new cute.ui.tabview.TabView();
      this.add(container);

      // Create a list of tab-names and order them
      var exten_list = new Array(this._object.baseType);
      var tmp = qx.lang.Object.getKeys(this._object.extensionTypes);
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
  
      // Handle type independent widget settings
      var attribute_defs = this.getAttributeDefinitions_();
      for(var name in attribute_defs){
        var attrs = attribute_defs[name];

        var widgetName = qx.lang.Object.getKeyFromValue(this._bindings, name);

        if (widgetName){
          var widget = this._widgets[widgetName];

          // Read-only?
          if (attrs['readonly'] === true){
            widget.setReadOnly(true);
          }

          // Required?
          if (attrs['mandatory'] === true) {
            this.setWidgetRequired(name, true);
          }

          // Toggler
          if (qx.lang.Object.getKeys(attrs['blocked_by']).length > 0) {

            this._processBlockedBy(widget, attrs['blocked_by']);
          }
        } else {
          this.warn("skipping attribute " +  name + " - no binding found");
        }
      }

      // Add button static button line for the moment
      var paneLayout = new qx.ui.layout.HBox().set({
        spacing: 4,
        alignX : "right"
      });
      var buttonPane = new qx.ui.container.Composite(paneLayout).set({
        paddingTop: 11
      });

      var okButton = cute.ui.base.Buttons.getOkButton();
      this.__okBtn = okButton;
      this.__okBtn.setEnabled(false);
      okButton.addState("default");
      buttonPane.add(okButton);

      okButton.addListener("click", function() {
        this._object.commit(function(result, error){
          if(error){
            if(error.field){
              this._object.fireDataEvent("propertyUpdateOnServer", {success: !error, error: error, property: error.field});
            }else{
              new cute.ui.dialogs.Error(error.message).open();
            }
          }else{
            this._object.close(function(result, error){
              if(error){
                new cute.ui.dialogs.Error(error.message).open();
              }else{
                this.fireEvent("done");
              }
            }, this);
          }
        }, this);
      }, this);

      var cancelButton = cute.ui.base.Buttons.getCancelButton();
      this.__cancelBtn = cancelButton;
      buttonPane.add(cancelButton);

      cancelButton.addListener("click", function() {
        this._object.close(function(result, error){
          if(error){
            new cute.ui.dialogs.Error(error.message).open();
          }
        }, this);
        this.fireEvent("done");
      }, this);

      this.add(buttonPane);

      return true;
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
      var func = function(match, values, widget){
          for(var i=0; i< values.length; i++){
            if(match == values[i]){
              widget.block();
              return;
            }
          }
          widget.unblock(true);
        };
     
      /* Extract information about when to block the widget
       * and add a listener to the sourceo-widget, to check
       * its values again after they were modified.
       * (right now we only support one block-definition)
       * */
      data = data[0];
      var name = data['name'];
      try{
        var value = data['value'];
        this._widgets[name].addListener("changeValue", function(e){
            func(value, e.getData().toArray(), widget);
          }, this);

        // Initially check blocking
        func(value, this._object.get(name).toArray(), widget);

      }catch(e){
        this.error("Failed to execute blocking for not existing widget: " + name) ;
      }
    },

    executeAction : function(dialog, target, icon)
    {
      if (dialog) {
        this.debug("launch dialog named: cute.ui.dialogs." + dialog);

        if (cute.ui.dialogs[dialog]) {
          var dialogW = new cute.ui.dialogs[dialog](this._object);
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
            var data = this._object[match[1]];
            if (typeof data === 'string') {
              params[i] = params[i].replace(match[0], data);
            } else {
              params[i] = params[i].replace(match[0], data[0]);
            }
          }
        }
        
        params.unshift(method, function(result, error) {
          if (error) {
            new cute.ui.dialogs.Error(error.message).open();
          } else {
            this.debug("call method " + target + " on object returned with: " + result);
          }
        }, this);

        this._object.callMethod.apply(this._object, params);
      }
    },

    _makeExtensionMenuEntry : function(ext, props, resources) {
      var eb = new qx.ui.menu.Button(this.tr(this.getStringProperty('windowTitle', props)),
        this.getIconProperty('windowIcon', props, resources));
      eb.addListener("execute", function() {
        this.extendObjectWith(ext);
      }, this);

      return eb;
    },

    _makeRetractMenuEntry : function(ext, props, resources) {
      var eb = new qx.ui.menu.Button(this.tr(this.getStringProperty('windowTitle', props)),
        this.getIconProperty('windowIcon', props, resources));
      eb.addListener("execute", function() {
        this.retractObjectFrom(ext);
      }, this);

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

      var label = this.tr(this.getStringProperty("text", props));
      var icon = this.getIconProperty("icon", props, resources);
      var dialog = this.getStringProperty("dialog", props);
      var target = this.getStringProperty("target", props);
      var shortcut = this.getStringProperty("shortcut", props);
      var condition = this.getStringProperty("condition", props);

      // Check if we need to add a global shortcut
      if (shortcut) {
        //TODO: collect for dispose
        var hotkey = new qx.ui.core.Command(shortcut);
        hotkey.addListener("execute", function() {this.executeAction(dialog, target, icon);}, this);
      }

      // Evaluate enabled state
      var enabled = undefined;
      var eb = new qx.ui.menu.Button(label, icon);

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

          // Collect agruments that have to be passed to the method call.
          var attrs = state[4].split(",");
          var args = [];
          
          for(var item in attrs){
        	var value;
            if(attrs[item] == "dn" || attrs[item] == "uuid"){
              value = this._object[attrs[item]];
            }else{
              value = this._object.get(attrs[item]).toArray();
              if(value.length){
                value = value[0];
              }else{
                value = null;
              }
            }
            args.push(value);
          }

          // Now execute the method with its arguments and let the callback
          // set the button state
          var rpc = cute.io.Rpc.getInstance();
          rpc.cA.apply(rpc, [function(result, error){
              result = (state[1] == "!") ? !result : result;
              eb.setEnabled(result);
            }, this, method].concat(args));

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
      eb.addListener("execute", function() {
        this.executeAction(dialog, target, icon);
      }, this);

      return eb;
    },

    getTranslatedExtension : function(ext)
    {
      if (!this._translated_extensions[ext]) {
        var nodes = qx.xml.Document.fromString(this._object.templates[ext]);
        var widget = nodes.firstChild.getElementsByTagName("widget").item(0).childNodes;
        this._translated_extensions[ext] = this.getStringProperty("windowTitle", this.extractProperties(widget));
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
      var actionMenu = new qx.ui.menu.Menu();
      var ui_s = this._object.templates[this._object.baseType];
      for (var i=0; i<ui_s.length; i++) {
        var nodes = qx.xml.Document.fromString(ui_s[i]);
        var actions = nodes.firstChild.getElementsByTagName("action");
        for (var i=0; i<actions.length; i++) {
          actionMenu.add(this._makeActionMenuEntry(actions[i]));
        }
      }

      var extendMenu = new qx.ui.menu.Menu();
      var retractMenu = new qx.ui.menu.Menu();

      for (var ext in this._object.extensionTypes) {
        if (this._object.templates[ext] && this._object.templates[ext].length != 0) {

          // Find first widget definition and extract windowIcon and windowTitle
          var ui_s = this._object.templates[ext];
          var added = false;
          for (var i=0; i<ui_s.length; i++) {
            var nodes = qx.xml.Document.fromString(ui_s[i]);
            var resources = this.extractResources(nodes.childNodes, cute.Config.getTheme());
            var widget = nodes.firstChild.getElementsByTagName("widget").item(0).childNodes;
            var props = this.extractProperties(widget);

            if (this._object.extensionTypes[ext]) {
              if (!added) {
                retractMenu.add(this._makeRetractMenuEntry(ext, props, resources));
                added = true;
              }

            } else {
              if (!added) {
                extendMenu.add(this._makeExtensionMenuEntry(ext, props, resources));
                added = true;
              }

              // Find extension level actions
              var actions = nodes.firstChild.getElementsByTagName("action");
              for (var i=0; i<actions.length; i++) {
                actionMenu.add(this._makeActionMenuEntry(actions[i], resources));
              }
            }
          }
        }
      }

      if (extendMenu.hasChildren()) {
        this._extendButton = new qx.ui.menu.Button(this.tr("Extend"), cute.Config.getImagePath("actions/extend.png", 22), null, extendMenu);
        this.__toolMenu.add(this._extendButton);
      }

      if (retractMenu.hasChildren()) {
        this._retractButton = new qx.ui.menu.Button(this.tr("Retract"), cute.Config.getImagePath("actions/retract.png", 22), null, retractMenu);
        this.__toolMenu.add(this._retractButton);
      }

      if (actionMenu.hasChildren()) {
        this._actionButton = new qx.ui.menu.Button(this.tr("Action"), cute.Config.getImagePath("actions/actions.png", 22), null, actionMenu);
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
          this.error(error.message);
        } else {

          // Remove all widget references and then close the page
          for(var widget in this._extension_to_widgets[extension]){
            widget = this._extension_to_widgets[extension][widget];
            delete this._widgets[widget];
          }
          delete this._extension_to_widgets[extension];

          var pages = this._extension_to_page[extension];
          for (var i = 0; i<pages.length; i++) {
            pages[i].fireEvent("close");
            pages[i].dispose();
            this._object.refreshMetaInformation(this._updateToolMenu, this);
            this.setModified(true);

            if (callback) {
                callback();
            }
          }

          delete this._extension_to_page[extension];
        }
      }, this, extension);
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
          if (this._object.extensionTypes[ext] && this._object.templates[ext] && this._object.templates[ext].length != 0) {
            needed.push(ext);
          }
        }

        // Ask user to enable the remaining dependencies
        if (needed.length != 0) {
          var dlg = new cute.ui.dialogs.Dialog(this.trn("Dependent extension", "Dependent extensions", needed.length),
                  cute.Config.getImagePath("status/dialog-warning.png", 22));
          dlg.setWidth(400);

          var lst = "<ul>";
          for (var i = 0; i<needed.length; i++) {
            lst += "<li><b>" + this.getTranslatedExtension(needed[i]) + "</b></li>";
          }
          lst += "</ul>";

          var message = new qx.ui.basic.Label(
            this.trn("To retract the <b>%1</b> extension from this object, the following additional extension needs to be removed: %2",
                     "To retract the <b>%1</b> extension from this object, the following additional extensions need to be removed: %2",
                     needed.length, this.getTranslatedExtension(extension), lst) +
            this.trn("Do you want the dependent extension to be removed?", "Do you want the dependent extensions to be removed?", needed.length)
          );
          message.setRich(true);
          message.setWrap(true);

          dlg.addElement(message);

          var ok = cute.ui.base.Buttons.getOkButton();
          ok.addListener("execute", function() {
            var queue = [];
            for (var i = 0; i<needed.length; i++) {
              queue.push([this._retractObjectFrom, this, [needed[i]]]);
            }

            queue.push([this._retractObjectFrom, this, [extension]]);
            cute.Tools.serialize(queue);

            dlg.close();
          }, this);

          dlg.addButton(ok);
          var cancel = cute.ui.base.Buttons.getCancelButton();
          cancel.addListener("execute", dlg.close, dlg);
          dlg.addButton(cancel);

          dlg.show();

          return;
        }

      }

      // Setup new tab
      this._retractObjectFrom(extension);
    },

    _extendObjectWith : function(extension, callback) {
      this._object.extend(function(result, error) {
        if (error) {
          this.error(error.message);
        } else {
          //TODO: bind new properties
          this._createTabsForExtension(extension);
          this._object.refreshMetaInformation(this._updateToolMenu, this);
          this.setModified(true);

          if (callback) {
            callback();
          }
        }
      }, this, extension);
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
          var dlg = new cute.ui.dialogs.Dialog(this.trn("Missing extension", "Missing extensions", needed.length),
                  cute.Config.getImagePath("status/dialog-warning.png", 22));
          dlg.setWidth(400);

          var lst = "<ul>";
          for (var i = 0; i<needed.length; i++) {
            lst += "<li><b>" + this.getTranslatedExtension(needed[i]) + "</b></li>";
          }
          lst += "</ul>";

          var message = new qx.ui.basic.Label(
            this.trn("To extend the object by the <b>%1</b> extension, the following additional extension is required: %2",
                     "To extend the object by the <b>%1</b> extension, the following additional extensions are required: %2",
                     needed.length, this.getTranslatedExtension(type), lst) +
            this.trn("Do you want the missing extension to be added?", "Do you want the missing extensions to be added?", needed.length)
          );
          message.setRich(true);
          message.setWrap(true);

          dlg.addElement(message);

          var ok = cute.ui.base.Buttons.getOkButton();
          ok.addListener("execute", function() {
            var queue = [];

            // Setup additional tab(s)
            for (var i = 0; i<needed.length; i++) {
              queue.push([this._extendObjectWith, this, [needed[i]]]);
            }

            // Setup desired tab
            queue.push([this._extendObjectWith, this, [type]]);
            cute.Tools.serialize(queue);

            dlg.close();
          }, this);
          dlg.addButton(ok);
          var cancel = cute.ui.base.Buttons.getCancelButton();
          cancel.addListener("execute", dlg.close, dlg);
          dlg.addButton(cancel);

          dlg.show();

          return;
        }

      }

      // Setup new tab
      this._extendObjectWith(type);
    },


    /* Create the gui elements for the given extension
     * and appends a new page the tab-container.
     * */
    _createTabsForExtension: function(extension){
      this._extension_to_page[extension] = [];

      // Process each tab of the current extension
      var ui_definition = this.getUiDefinition_();
      for (var tab=0; tab<ui_definition[extension].length; tab++) {

        // Clean-up values that were collected per-loop.
        this._current_widgets = [];
        this._current_bindings = {};
        this._current_tabstops = new Array();
        this._current_buddies = {};

        // Parse the ui definition of the object
        var ui_def = qx.xml.Document.fromString(ui_definition[extension][tab]).childNodes;
        var resources = this.extractResources(ui_def, cute.Config.getTheme());
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
          var page = new qx.ui.tabview.Page(this.tr(info['widget'].title_), info['widget'].icon_);
          page.setLayout(new qx.ui.layout.VBox());
          page.add(info['widget']);
          this._extension_to_page[extension].push(page);

          // Create a mapping from widget to page
          for(item in this._current_widgets){
            var widgetName = this._current_bindings[this._current_widgets[item]];
            this._widget_to_page[widgetName] = page;
          }

          // Add "remove extension" buttons to all non-base tabs.
          if (extension != this._object.baseType) {
            page.setShowCloseButton(true);
            page.setUserData("type", extension);

            var closeButton = page.getButton();
            closeButton.getChildControl("close-button").setToolTip(new qx.ui.tooltip.ToolTip(this.tr("Remove extension")));
            closeButton.removeListener("close", page._onButtonClose, page);
            closeButton.addListener("close", function() {
              this.retractObjectFrom(page.getUserData("type"));
            }, this);
          }

          // Add the page to the gui
          this._tabContainer.add(page);

          // Connect this master-widget with the object properties, establish tabstops
          this.processTabStops(this._current_tabstops);

          // Transmit object property definitions to the widgets
          for(var item in this._widgets){
            this.processWidgetProperties(item);
          }

          this.processBuddies(this._current_buddies);
          this.processBindings(this._current_bindings);

        } else {
          this.info("*** no widget found for '" + extension + "'");
        }
      }
    },


    /* Transfer collected widget-properties to the widgets.
      */
    processWidgetProperties: function(item){
      var w = this._widgets[item];
      var widgetName = this._bindings[item];
      var defs = this.getAttributeDefinitions_()[widgetName];

      if(w && w.hasState("cuteWidget")){
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

              } else if (layout_type == "QHBoxLayout") {
                var wdgt = this.processElements(loc, topic.childNodes);
                widget.add(wdgt['widget'], {flex: this.extractHFlex(wdgt['properties'])});

              } else if (layout_type == "QVBoxLayout") {
                var wdgt = this.processElements(loc, topic.childNodes);
                widget.add(wdgt['widget'], {flex: this.extractVFlex(wdgt['properties'])});
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
      if (cute.ui.widgets[classname]) {
        widget = new cute.ui.widgets[classname];
        this._widgets[name] = widget;
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
              widget.getLayout().setColumnFlex(column, 1);

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
              widget.add(wdgt['widget']);

            } else if (layout_type == "QVBoxLayout") {
              var wdgt = this.processElements(loc, topic.childNodes);
              widget.add(wdgt['widget']);
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
      var widget = new qx.ui.groupbox.GroupBox(this.tr(title));
      this.processCommonProperties(name, widget, props);
      this._widgets[name] = widget;
      this.__add_widget_to_extension(name, loc);

      return widget;
    },

    processCommonProperties : function(name, widget, props)
    {
      // Set geometry
      var geometry = this.getGeometryProperty('geometry', props);
      if (geometry) {
        widget.setWidth(geometry['width']);
        widget.setHeight(geometry['height']);
      }

      // Set tooltip
      var tooltip = this.getStringProperty('toolTip', props);
      if (tooltip != null) {
        widget.setToolTip(new qx.ui.tooltip.ToolTip(this.tr(tooltip)));
      }

      // Set ro mode
      var readonly = this.getBoolProperty('readOnly', props);
      if (readonly != null) {
        widget.setReadOnly(readonly);
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

    setWidgetInvalidMessage : function(name, message)
    {
      var widgetName = qx.lang.Object.getKeyFromValue(this._bindings, name);
      if (this._widgets[widgetName]) {
        this._widgets[widgetName].setInvalidMessage(message);
      } else {
        this.error("*** cannot set invalid message for non existing widget '" + name + "'!");
      }
    },

    setWidgetValid: function(name, flag)
    {
      var widgetName = qx.lang.Object.getKeyFromValue(this._bindings, name);
      if (this._widgets[widgetName]) {
        this._widgets[widgetName].setValid(flag);
      } else {
        this.error("*** cannot set valid flag for non existing widget '" + name + "'!");
      }
    },

    resetWidgetInvalidMessage : function(name)
    {
      var widgetName = qx.lang.Object.getKeyFromValue(this._bindings, name);
      if (this._widgets[widgetName]) {
        this._widgets[widgetName].resetInvalidMessage();
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
        if (resources[props[what]['iconset']['normaloff']]) {
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

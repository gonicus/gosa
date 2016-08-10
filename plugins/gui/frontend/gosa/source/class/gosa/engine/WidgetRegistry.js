qx.Class.define("gosa.engine.WidgetRegistry", {
  extend : qx.core.Object,
  type : "singleton",

  construct : function() {
    this._registry = {};
    this._buddies = {};
  },

  members : {
    _registry : null,
    _buddies : null,

    /**
     * creates all the widgets from a given "content",
     * in most cases it will be a parsed template,
     * and save it under the given context. For now, it's
     * the plain filename
     *
     * @param context {String} The name of the context  
     * @param content {Object} The widgets description (from a template)
     */
    addContext : function(context, content){
      qx.core.Assert.assertString(context);
      var container = null;
      if (!this._registry.hasOwnProperty(context)) {
        var templateProcessor = gosa.engine.ProcessorFactory.getProcessor(content, context);
        
        container = new qx.ui.container.Composite(new qx.ui.layout.VBox());
        container.setMaxWidth(600);

        templateProcessor.setTarget(container);
        templateProcessor.process(content);
      }
    },

    /**
     * Remove the whole context from the registry
     *
     * @param context {String} The name of the context  
     */
    removeContext : function(context){
      qx.core.Assert.assertString(context);

      if (this._registry.hasOwnProperty(context)) {
        delete this._registry[context];
      }
      if (this._buddies.hasOwnProperty(context)) {
        delete this._buddies[context];
      }
    },

    /**
     * get all the widgets from a specific context
     *
     * @param context {String} The name of the context  
     * @return {Array} The widget the array of widgets or an empty array
     */
    getContext : function(context){
      if (!this._registry.hasOwnProperty(context)) {
        return [];
      }
      return this._registry[context];
    },

    /**
     * Saves a widget in the registry.
     *
     * @param context {String} The context under which the widget shall be saved
     * @param widget {qx.ui.core.Widget} The widget
     */
    addWidget : function(context, widget) {
      qx.core.Assert.assertString(context);
      qx.core.Assert.assertQxWidget(widget);

      if (!this._registry.hasOwnProperty(context)) {
        this._registry[context] =[] 
      }

      this._registry[context].push(widget);
    },

    /**
     * Saves a widget in buddies object.
     *
     * @param context {String} The context under which the widget shall be saved
     * @param path {String} The path under which the widget shall be saved
     * @param widget {qx.ui.core.Widget} The widget
     */
    addBuddy: function(context, path, widget) {
      qx.core.Assert.assertString(context);
      qx.core.Assert.assertString(path);
      qx.core.Assert.assertQxWidget(widget);

      if (!this._buddies.hasOwnProperty(context)) {
        this._buddies[context] = {};
      }

      if (!this._buddies[context].hasOwnProperty(path)) {
        this._buddies[context][path] = {};
      }

      this._buddies[context][path].buddy = widget;
    },

    /**
     * Saves a widget in mates object.
     *
     * @param context {String} The context under which the widget shall be saved
     * @param path {String} The path under which the widget shall be saved
     * @param widget {qx.ui.core.Widget} The widget
     */
    addMate: function(context, path, widget) {
      qx.core.Assert.assertString(context);
      qx.core.Assert.assertString(path);
      qx.core.Assert.assertQxWidget(widget);

      if (!this._buddies.hasOwnProperty(context)) {
        this._buddies[context] = {};
      }

      if (!this._buddies[context].hasOwnProperty(path)) {
        this._buddies[context][path] = {};
      }

      if (!this._buddies[context][path].hasOwnProperty('mates')) {
        this._buddies[context][path].mates = [];
      }

      this._buddies[context][path].mates.push(widget);
    },

    /**
     * remove buddies
     *
     * @param context {String} the context to remove buddies from
     * @param path {String} the buddies modelPath
     */
    removeBuddiesByPath : function(context, path){
      qx.core.Assert.assertString(context);
      qx.core.Assert.assertString(path);

      if (this._buddies.hasOwnProperty(context) && this._buddies[context].hasOwnProperty(path)) {
        delete this._buddies[context][path];
      }
    },

    /**
     * remove mates
     *
     * @param context {String} the context to remove your buddy mates from
     * @param path {String} the buddies modelPath
     */
    removeMatesByPath : function(context, path){
      qx.core.Assert.assertString(context);
      qx.core.Assert.assertString(path);

      if (this._buddies.hasOwnProperty(context) && 
          this._buddies[context].hasOwnProperty(path) && 
          this._buddies[context][path].hasOwnProperty('mates')) {
        delete this._buddies[context][path].mates;
      }
    },

    /**
     * remove a buddy's mate
     *
     * @param context {String} the context to remove your buddy mates from
     * @param path {String} the buddies modelPath
     */
    removeMateByPath : function(context, path, widget){
      qx.core.Assert.assertString(context);
      qx.core.Assert.assertString(path);
      qx.core.Assert.assertQxWidget(widget);

      if (this._buddies.hasOwnProperty(context) && 
          this._buddies[context].hasOwnProperty(path) && 
          this._buddies[context][path].hasOwnProperty('mates')) {

        qx.lang.Array.remove(this._buddies[context][path].mates, widget);
      }
    },

    /**
     * Get all the buddies and their mates for a specific context
     *
     * @param context {String} the name of the widgets context you want to return
     * @return {Array} the context of widgets to return or an empty object 
     */
    getBuddies : function(context){
      qx.core.Assert.assertString(context);

      if (this._buddies.hasOwnProperty(context)) {
        return this._buddies[context];
      }

      return {};
    },

    /**
     * Returns the buddy and its mates in an object
     *
     * @param context {String} The name of the context 
     * @param name {String} The name/modelPath/buddyModelPath of the widgets
     * @return {widget} widget or null
     */
    getBuddiesByPath : function(context, path) {
      qx.core.Assert.assertString(context);
      qx.core.Assert.assertString(path);

      if (this._buddies.hasOwnProperty(context) && this._buddies[context].hasOwnProperty(path)) {
        return this._buddies[context][path];
      }
      return {};
    },

    /**
     * Removes a single widget from the registry and buddies
     *
     * @param widget {qx.ui.core.Widget} The widget that shall be removed
     */
    removeWidget : function(widget) {
      qx.core.Assert.assertQxWidget(widget);

      var arr;
      for (var context in this._registry) {
        arr = this._registry[context];
        qx.lang.Array.remove(arr, widget);
        if (arr.length === 0)  {
          delete this._registry[context];
        }
      }

      Object.keys(this._buddies).forEach(function(context){
          
        Object.keys(this._buddies[context]).forEach(function(path){
          if (this._buddies[context][path].hasOwnProperty('buddy') &&
              this._buddies[context][path].buddy === widget) {
            delete this._buddies[context][path].buddy;
          }
          if (this._buddies[context][path].hasOwnProperty('mates')) {
            arr = this._buddies[context][path].mates;
            qx.lang.Array.remove(arr, widget);
            if (arr.length === 0) {
              delete this._buddies[context][path].mates;
            }
          }

          if (qx.lang.Object.isEmpty(this._buddies[context][path])) {
            delete this._buddies[context][path];
          }
        }, this);

        if (qx.lang.Object.isEmpty(this._buddies[context])) {
          delete this._buddies[context];
        }
      }, this);
    },

    /**
     * Connect buddies and mates
     */
    connectBuddies : function(){
      Object.keys(this._buddies).forEach(function(context){
        Object.keys(this._buddies[context]).forEach(function(path){
          if (this._buddies[context][path].hasOwnProperty('buddy') &&
              this._buddies[context][path].hasOwnProperty('mates')) {
            var mates = this._buddies[context][path].mates;
            for (var mate in mates) {
              mates[mate].setBuddy(this._buddies[context][path].buddy);
            }
          }
        }, this);
      }, this);
    }
  },

  destruct : function() {
    this._disposeObjects("_registry");
    this._disposeObjects("_buddies");
  }
});

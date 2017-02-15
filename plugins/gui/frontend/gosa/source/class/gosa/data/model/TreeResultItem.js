/*
 * This file is part of the GOsa project -  http://gosa-project.org
 *
 * Copyright:
 *    (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de
 *
 * License:
 *    LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
 *
 * See the LICENSE file in the project's top-level directory for details.
 */

qx.Class.define("gosa.data.model.TreeResultItem",
{
  extend : qx.core.Object,

  include: [qx.data.marshal.MEventBubbling],

  construct: function(title, prnt){
    this.base(arguments);

    if(prnt){
      this.setParent(prnt);
    }

    if(title){
      this.setTitle(title);
    }

    this.setChildren(new qx.data.Array());
    this.setLeafs(new qx.data.Array());
  },

  events : {
    "updatedItems" : "qx.event.type.Event"
  },

  properties : {

    moveTargetFor: {
      check: "String",
      nullable: true,
      event: "changeMoveTargetFor"
    },

    moveTarget: {
      check: "Boolean",
      init: false,
      event: "changeMoveTarget"
    },

    container : {
      check : "Boolean",
      event : "changeContainer",
      init : false
    },

    open : {
      check : "Boolean",
      event : "changeOpen",
      apply : "_onOpen",
      init : false
    },

    loaded : {
      check : "Boolean",
      event : "changeLoaded",
      init : false
    },

    loading : {
      check : "Boolean",
      event : "changeLoading",
      init : false
    },

    hasChildren : {
      check : "Boolean",
      event : "changeHasChildren",
      init : false
    },

    parent : {
      event : "changeParent",
      init : null
    },

    children : {
      check : "Array",
      event : "changeChildren",
      apply: "_applyEventPropagation",
      init : null
    },

    leafs : {
      check : "Array",
      event : "changeLeafs",
      init : null
    },

    title : {
      check : "String",
      event : "changeTitle",
      init : ""
    },

    dn : {
      check : "String",
      event : "changeDn",
      init : ""
    },

    uuid : {
      check : "String",
      event : "changeUuid"
    },

    type : {
      check : "String",
      event : "changeType",
      init : null
    },

    description : {
      check : "String",
      event : "changeDescription",
      init : ""
    }
  },

  members: {

    _onOpen : function(value){

      if(!this.isLoaded() && value){
        // this.getChildren().removeAll();
        // this.getLeafs().removeAll();
        this.load();
      }
    },

    unload: function() {
      this.setLoaded(false);
      this.setLoading(false);
      this.getChildren().removeAll();
      this.getLeafs().removeAll();
    },

    reload : function() {
      this.unload();
      return this.load();
    },

    load: function() {

      return new qx.Promise(function(resolve, reject) {
        // If currently loading, delay ready
        if (this.isLoading()) {
          this.addListenerOnce("changeLoading", resolve, this);
        }

        // If not done yet, resolve the child elements of this container
        else if (this.isLoaded()) {
          resolve();
        }
        else {

          this.setLoading(true);

          var rpc = gosa.io.Rpc.getInstance();
          if (this.getParent()) {
            var promise = null;
            // We're looking for entries on the current base
            if (this.getMoveTargetFor() !== null) {
              promise = rpc.cA("getContainerTree", this.getDn(), this.getMoveTargetFor());
            }
            else {
              promise = rpc.cA("search", this.getDn(), "children", null, {
                secondary : false,
                'adjusted-dn' : true,
                actions : true
              })
            }
            return promise.then(function(data) {
              var newc = new qx.data.Array();
              var newl = new qx.data.Array();
              for (var id in data) {
                if (data.hasOwnProperty(id)) {
                  var item = this.parseItemForResult(data[id]);
                  if (item.isContainer()) {
                    newc.push(item);
                  }
                  else {
                    newl.push(item);
                  }
                }
              }
              this.setChildren(newc);
              this.setLeafs(newl);
              this.sortElements();
              this.setLoaded(true);
              resolve();
              this.setLoading(false);
            }, this)
            .catch(reject);
          }
          else {
            // We're added upon the root
            // Fetch all available domains
            return rpc.cA("getEntryPoints").then(function(entries) {
              return qx.Promise.map(entries, function(entry) {
                return rpc.cA("search", entry, "base", null, {
                  secondary : false,
                  'adjusted-dn' : true,
                  actions : true
                });
              }, this);
            }, this)
            .then(function(results) {
              var newc = new qx.data.Array();
              results.forEach(function(result) {
                var item = this.parseItemForResult(result[0]);
                newc.push(item);
              }, this);
              this.sortElements();

              this.setChildren(newc);
              // Stop loading throbber
              this.setLoaded(true);
              this.setLoading(false);

              resolve()
            }, this)
            .catch(function(error) {
              this.error("could not resolve tree element '" + error + "'!");
              reject();
            }, this);
          }
        }
      }, this);
    },

    /**
     *  Sort child and leaf elements
     */
    sortElements : function(){
      var sortF= function(a,b) {
        if(a.getTitle() == b.getTitle()){
          return 0;
        }
        return (a.getTitle() < b.getTitle()) ? -1 : 1;
      };
      this.getChildren().sort(sortF);
      this.getLeafs().sort(sortF);
      this.fireEvent("updatedItems");
    },

    /**
     *  Parses a result item into a TreeResultItem
     */
    parseItemForResult: function(result){
      var item = new gosa.data.model.TreeResultItem(result['title'], this).set({
          container: !!result['container'],
          dn: result['dn'],
          description: result['description'],
          title: result['title'],
          type: result['tag'],
          uuid: result['uuid']
        });
      if (this.getMoveTargetFor() !== null) {
        if ('allowed_move_target' in result) {
          item.setMoveTarget(result['allowed_move_target']);
        }
        this.bind("moveTargetFor", item, "moveTargetFor");
      }

      // Add a dummy object if we know that this container has children.
      if(result['hasChildren']){
        item.setHasChildren(true);
        item.getChildren().push(new gosa.data.model.TreeResultItem("Dummy"));
      }

      return(item);
    },

    /**
     * Returns a table row
     */
    getTableRow: function(){
      return({
        type: this.getType(),
        title: this.getTitle(),
        description: this.getDescription(),
        dn:  this.getDn(),
        uuid: this.getUuid()
      });
    }
  }
});

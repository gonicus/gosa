qx.Interface.define("gosa.engine.extensions.IExtension", {

  members : {
    process : function(data, target) {
      this.assertQxObject(target);
    }
  }
});

qx.Class.define("gosa.Tools", {

  type: "static",

  statics: {

    createActionUrl: function(action, target){
      var url = document.location.origin + document.location.pathname;
      url += "#" + action + gosa.Config.actionDelimiter + target;
      return(url);
    },

    getLocale: function(){
      var locale;
      if (gosa.Config.locale) {
        locale = gosa.Config.locale;
      } else {
        locale = qx.bom.client.Locale.getLocale();
        var variant = qx.bom.client.Locale.getVariant();
        if (locale && variant) {
          locale = locale + "-" + variant;
        }
      }
      return(locale);
    },

    serialize : function(queue)
    {
        var timer = qx.util.TimerManager.getInstance();
        var locked = false;

        timer.start(function(userData, timerId){
            if (locked) {
                return;
            } 

            locked = true;

            var entry = queue.shift();
            if (entry == undefined) {
                timer.stop();
                return;
            }

            var func = entry[0];
            var context = entry[1];
            var params = entry[2];
            params.push(function() {
                locked = false;
            });
            func.apply(context, params);
        }, 10, null, null, 0);
    }
  }
});

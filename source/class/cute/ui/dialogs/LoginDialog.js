qx.Class.define("cute.ui.dialogs.LoginDialog",
{
  extend : cute.ui.dialogs.Dialog,

  construct : function()
  {
    this.base(arguments, this.tr("Login"));

    /* Container layout */
    var layout = new qx.ui.layout.Grid(9, 5);
    layout.setColumnAlign(0, "right", "top");
    layout.setColumnAlign(2, "right", "top");
    this.setLayout(layout);

    /* Try to receive currently loggedin user */
    this.add(new qx.ui.basic.Label(this.tr("Name")).set({allowShrinkX : false, paddingTop : 3}), {row: 0, column: 0});
    this.add(new qx.ui.basic.Label(this.tr("Password")).set({allowShrinkX : false, paddingTop : 3}), {row: 1, column: 0});

    var username = new qx.ui.form.TextField();
    var password = new qx.ui.form.PasswordField();
    var info = new qx.ui.basic.Label().set({rich : true, alignX : "left"});

    this.add(username.set({allowGrowX: true, allowShrinkX: true, width: 200}), {row: 0, column: 1});
    this.add(password.set({allowGrowX : true, allowShrinkX : true, width : 200}), {row : 1, column : 1});
    this.add(info, {row : 3, column  : 0, colSpan : 2});

    var login = new qx.ui.form.Button(this.tr("Login"));
    login.setAllowStretchX(false);
    this.add(login, {row : 5, column : 0});

    login.addListener("execute", function(){
      if (cute.Config.notifications) {
          if (cute.Config.notifications.checkPermission() != 0) {
              cute.Config.notifications.requestPermission();
        }
      }

      var rpc = cute.io.Rpc.getInstance();
      var that = this;
      rpc.callAsync(function(result, error){
        if(!result){
          info.setValue(that.tr("Invalid login ..."));
        }else{
          that.close();
          that.fireEvent("login");
        }
      }, "login", username.getValue(), password.getValue());
    }, this);

    this.setFocusOrder([username, password, login]);

    if(qx.core.Environment.get("qx.debug")){
      username.setValue(cute.LocalConfig.user);
      password.setValue(cute.LocalConfig.password);
      login.execute();
    }
  },

  events: {
    "login": "qx.event.type.Event"
  }
});


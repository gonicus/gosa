qx.Class.define("gosa.test.engine.SymbolTableTest",
{
  extend : qx.dev.unit.TestCase,

  members :
  {
    testAddResolveSymbolTest : function() {
      var symTbl = gosa.engine.SymbolTable.getInstance();

      // no entry
      this.assertUndefined(symTbl.resolveSymbol("foo"));

      // entry
      symTbl.addSymbol("foo", "bar");
      this.assertException(function() {symTbl.addSymbol("foo", "bar");});
      this.assertEquals("bar", symTbl.resolveSymbol("foo"));
      this.assertUndefined(symTbl.resolveSymbol("bar"));
    }
  }
});

/*    */ package rockyhockey.gui.mvc;
/*    */ 
/*    */ import java.io.InputStream;
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ public final class ResourceLoader
/*    */ {
/*    */   public static InputStream load(String path) {
/* 19 */     InputStream input = ResourceLoader.class.getResourceAsStream(path);
/* 20 */     if (input == null) {
/* 21 */       input = ResourceLoader.class.getResourceAsStream("/" + path);
/*    */     }
/* 23 */     return input;
/*    */   }
/*    */ }


/* Location:              /home/felix/Downloads/JavaGUI (Kopie).jar!/rockyhockey/gui/mvc/ResourceLoader.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */
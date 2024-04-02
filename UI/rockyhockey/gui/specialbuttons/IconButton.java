/*    */ package rockyhockey.gui.specialbuttons;
/*    */ 
/*    */ import javax.swing.ImageIcon;
/*    */ import javax.swing.JButton;
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
/*    */ public class IconButton
/*    */   extends JButton
/*    */ {
/*    */   private static final long serialVersionUID = 1L;
/*    */   
/*    */   public IconButton(ImageIcon icon) {
/* 21 */     setOpaque(false);
/* 22 */     setContentAreaFilled(false);
/* 23 */     setBorderPainted(false);
/* 24 */     setIcon(icon);
/* 25 */     setFocusPainted(false);
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public IconButton() {
/* 32 */     setOpaque(false);
/* 33 */     setContentAreaFilled(false);
/* 34 */     setBorderPainted(false);
/* 35 */     setFocusPainted(false);
/*    */   }
/*    */ }


/* Location:              /home/felix/Downloads/JavaGUI (Kopie).jar!/rockyhockey/gui/specialbuttons/IconButton.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */
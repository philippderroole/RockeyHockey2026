/*     */ package rockyhockey.gui.mvc;
/*     */ 
/*     */ import java.io.File;
/*     */ import java.io.FileReader;
/*     */ import java.io.FileWriter;
/*     */ import java.io.IOException;
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ public class HardwareIO
/*     */   implements Runnable
/*     */ {
/*     */   private static HardwareIO instance;
/*     */   private static final String GPIO_DIRECTORY = "/sys/class/gpio/";
/*     */   private volatile boolean playerLs;
/*     */   private volatile boolean botLs;
/*     */   
/*     */   public static HardwareIO getInstance() {
/*  27 */     if (instance == null) {
/*  28 */       instance = new HardwareIO();
/*     */     }
/*  30 */     return instance;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private HardwareIO() {
/*     */     try {
/*  38 */       if (!initGPIOasInput(5) || !initGPIOasInput(6)) {
/*  39 */         System.err.println("gpio fail");
/*     */       }
/*     */       
/*  42 */       Thread thread = new Thread(this);
/*  43 */       thread.start();
/*     */     }
/*  45 */     catch (IOException e) {
/*  46 */       e.printStackTrace();
/*     */     } 
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public boolean initGPIOasInput(int gpio) throws IOException {
/*  58 */     File gpioLocation = new File("/sys/class/gpio/gpio" + gpio + "/value");
/*  59 */     if (gpioLocation.exists()) {
/*  60 */       return true;
/*     */     }
/*  62 */     FileWriter fw = new FileWriter(new File("/sys/class/gpio/export"));
/*  63 */     fw.write(gpio);
/*  64 */     fw.close();
/*  65 */     return gpioLocation.exists();
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public boolean readGPIOSignal(int gpio) {
/*     */     try {
/*  75 */       FileReader fr = new FileReader(new File("/sys/class/gpio/gpio" + gpio + "/value"));
/*  76 */       char[] fileOut = new char[1];
/*  77 */       fr.read(fileOut);
/*  78 */       fr.close();
/*  79 */       return (fileOut[0] == '1');
/*     */     }
/*  81 */     catch (IOException e) {
/*  82 */       System.err.println("gpio fail");
/*  83 */       e.printStackTrace();
/*     */       
/*  85 */       return false;
/*     */     } 
/*     */   }
/*     */ 
/*     */ 
/*     */   
/*     */   public void resetOutput() {
/*  92 */     this.playerLs = false;
/*  93 */     this.botLs = false;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public boolean isPlayerLsActive() {
/* 101 */     if (this.playerLs) {
/* 102 */       this.playerLs = false;
/* 103 */       return true;
/*     */     } 
/* 105 */     return false;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public boolean isBotLsActive() {
/* 113 */     if (this.botLs) {
/* 114 */       this.botLs = false;
/* 115 */       return true;
/*     */     } 
/* 117 */     return false;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setPlayerLs() {
/* 124 */     this.playerLs = true;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setBotLs() {
/* 131 */     this.botLs = true;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void run() {
/*     */     try {
/* 141 */       long timeStemp = 0L;
/* 142 */       long currentTime = 0L;
/* 143 */       boolean playerWasHigh = false;
/* 144 */       boolean botWasHigh = false;
/*     */       while (true) {
/* 146 */         boolean gpio5 = readGPIOSignal(5);
/* 147 */         boolean gpio6 = readGPIOSignal(6);
/* 148 */         if (!playerWasHigh && gpio5) {
/* 149 */           if ((currentTime = System.currentTimeMillis()) - timeStemp > 2000L) {
/* 150 */             playerWasHigh = true;
/* 151 */             this.playerLs = true;
/* 152 */             timeStemp = currentTime;
/*     */           }
/*     */         
/*     */         }
/* 156 */         else if (!gpio5) {
/* 157 */           playerWasHigh = false;
/*     */         } 
/* 159 */         if (!botWasHigh && gpio6) {
/* 160 */           if ((currentTime = System.currentTimeMillis()) - timeStemp > 2000L) {
/* 161 */             botWasHigh = true;
/* 162 */             this.botLs = true;
/* 163 */             timeStemp = currentTime;
/*     */           }
/*     */         
/* 166 */         } else if (!gpio6) {
/* 167 */           botWasHigh = false;
/*     */         } 
/* 169 */         Thread.sleep(10L);
/*     */       }
/*     */     
/* 172 */     } catch (InterruptedException e) {
/* 173 */       e.printStackTrace();
/*     */       return;
/*     */     } 
/*     */   }
/*     */ }


/* Location:              /home/felix/Downloads/JavaGUI (Kopie).jar!/rockyhockey/gui/mvc/HardwareIO.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */
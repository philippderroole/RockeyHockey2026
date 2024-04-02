/*     */ package rockyhockey.gui.mvc;
/*     */ 
/*     */ import java.io.BufferedInputStream;
/*     */ import java.io.InputStream;
/*     */ import javax.sound.sampled.AudioInputStream;
/*     */ import javax.sound.sampled.AudioSystem;
/*     */ import javax.sound.sampled.Clip;
/*     */ import javax.sound.sampled.LineEvent;
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
/*     */ 
/*     */ 
/*     */ public class AudioThread
/*     */   extends Thread
/*     */   implements Runnable
/*     */ {
/*     */   private Clip soundClip;
/*     */   private InputStream soundInputStream;
/*     */   private String filename;
/*     */   private boolean loop;
/*     */   
/*     */   public static AudioThread playSound(String filename, boolean loop) {
/*  32 */     AudioThread soundThread = new AudioThread(filename, loop);
/*  33 */     soundThread.start();
/*  34 */     return soundThread;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static AudioThread playSound(String filename) {
/*  43 */     return playSound(filename, false);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private AudioThread(String filename, boolean loop) {
/*  52 */     this.filename = "/sounds/" + filename;
/*  53 */     this.loop = loop;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void run() {
/*     */     try {
/*  64 */       this.soundInputStream = ResourceLoader.load(this.filename);
/*     */       
/*  66 */       InputStream bufferedIn = new BufferedInputStream(this.soundInputStream);
/*     */       
/*  68 */       AudioInputStream inputStream = AudioSystem.getAudioInputStream(bufferedIn);
/*     */       
/*  70 */       this.soundClip = AudioSystem.getClip();
/*     */       
/*  72 */       this.soundClip.open(inputStream);
/*     */       
/*     */       try {
/*  75 */         synchronized (this) {
/*  76 */           if (this.loop) {
/*  77 */             this.soundClip.loop(-1);
/*     */             
/*  79 */             wait();
/*     */           } else {
/*     */             
/*  82 */             this.soundClip.loop(0);
/*  83 */             this.soundClip.addLineListener(event -> {
/*     */                   if (LineEvent.Type.STOP.equals(event.getType())) {
/*     */                     interrupt();
/*     */                   }
/*     */                 });
/*     */             
/*  89 */             wait(this.soundClip.getMicrosecondLength() / 1000L);
/*     */           }
/*     */         
/*     */         } 
/*  93 */       } catch (InterruptedException e) {
/*  94 */         System.out.println("stopped playing " + this.filename);
/*     */       } 
/*     */       
/*  97 */       this.soundClip.close();
/*  98 */       this.soundClip.flush();
/*     */     }
/* 100 */     catch (Exception e) {
/* 101 */       System.out.println("exception while playing: " + this.filename);
/* 102 */       System.out.println("exception type: " + e.getClass().getCanonicalName());
/* 103 */       System.out.println("message: " + e.getMessage());
/* 104 */       System.out.println();
/*     */     } 
/*     */   }
/*     */ }


/* Location:              /home/felix/Downloads/JavaGUI (Kopie).jar!/rockyhockey/gui/mvc/AudioThread.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */
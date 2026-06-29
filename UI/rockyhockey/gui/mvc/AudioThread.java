package rockyhockey.gui.mvc;

import java.io.BufferedInputStream;
import java.io.InputStream;
import javax.sound.sampled.AudioInputStream;
import javax.sound.sampled.AudioSystem;
import javax.sound.sampled.Clip;
import javax.sound.sampled.LineEvent;

public class AudioThread
        extends Thread
        implements Runnable {
    private Clip soundClip;
    private InputStream soundInputStream;
    private String filename;
    private boolean loop;

    public static AudioThread playSound(String filename, boolean loop) {
        AudioThread soundThread = new AudioThread(filename, loop);
        soundThread.start();
        return soundThread;
    }

    public static AudioThread playSound(String filename) {
        return playSound(filename, false);
    }

    private AudioThread(String filename, boolean loop) {
        this.filename = "/sounds/" + filename;
        this.loop = loop;
    }

    public void run() {
        try {
            this.soundInputStream = ResourceLoader.load(this.filename);

            InputStream bufferedIn = new BufferedInputStream(this.soundInputStream);

            AudioInputStream inputStream = AudioSystem.getAudioInputStream(bufferedIn);

            this.soundClip = AudioSystem.getClip();

            this.soundClip.open(inputStream);

            try {
                synchronized (this) {
                    if (this.loop) {
                        this.soundClip.loop(-1);

                        wait();
                    } else {

                        this.soundClip.loop(0);
                        this.soundClip.addLineListener(event -> {
                            if (LineEvent.Type.STOP.equals(event.getType())) {
                                interrupt();
                            }
                        });

                        wait(this.soundClip.getMicrosecondLength() / 1000L);
                    }

                }
            } catch (InterruptedException e) {
                System.out.println("stopped playing " + this.filename);
            }

            this.soundClip.close();
            this.soundClip.flush();
        } catch (Exception e) {
            System.out.println("exception while playing: " + this.filename);
            System.out.println("exception type: " + e.getClass().getCanonicalName());
            System.out.println("message: " + e.getMessage());
            System.out.println();
        }
    }
}
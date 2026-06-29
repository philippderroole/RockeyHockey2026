package rockyhockey.gui.mvc;

import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;

public class HardwareIO
        implements Runnable {
    private static HardwareIO instance;
    private static final String GPIO_DIRECTORY = "/sys/class/gpio/";
    private volatile boolean playerLs;
    private volatile boolean botLs;

    public static HardwareIO getInstance() {
        if (instance == null) {
            instance = new HardwareIO();
        }
        return instance;
    }

    private HardwareIO() {
        try {
            if (!initGPIOasInput(5) || !initGPIOasInput(6)) {
                System.err.println("gpio fail");
            }

            Thread thread = new Thread(this);
            thread.start();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public boolean initGPIOasInput(int gpio) throws IOException {
        File gpioLocation = new File("/sys/class/gpio/gpio" + gpio + "/value");
        if (gpioLocation.exists()) {
            return true;
        }
        FileWriter fw = new FileWriter(new File("/sys/class/gpio/export"));
        fw.write(gpio);
        fw.close();
        return gpioLocation.exists();
    }

    public boolean readGPIOSignal(int gpio) {
        try {
            FileReader fr = new FileReader(new File("/sys/class/gpio/gpio" + gpio + "/value"));
            char[] fileOut = new char[1];
            fr.read(fileOut);
            fr.close();
            return (fileOut[0] == '1');
        } catch (IOException e) {
            System.err.println("gpio fail");
            e.printStackTrace();

            return false;
        }
    }

    public void resetOutput() {
        this.playerLs = false;
        this.botLs = false;
    }

    public boolean isPlayerLsActive() {
        if (this.playerLs) {
            this.playerLs = false;
            return true;
        }
        return false;
    }

    public boolean isBotLsActive() {
        if (this.botLs) {
            this.botLs = false;
            return true;
        }
        return false;
    }

    public void setPlayerLs() {
        this.playerLs = true;
    }

    public void setBotLs() {
        this.botLs = true;
    }

    public void run() {
        try {
            long timeStemp = 0L;
            long currentTime = 0L;
            boolean playerWasHigh = false;
            boolean botWasHigh = false;
            while (true) {
                boolean gpio5 = readGPIOSignal(5);
                boolean gpio6 = readGPIOSignal(6);
                if (!playerWasHigh && gpio5) {
                    if ((currentTime = System.currentTimeMillis()) - timeStemp > 2000L) {
                        playerWasHigh = true;
                        this.playerLs = true;
                        timeStemp = currentTime;
                    }

                } else if (!gpio5) {
                    playerWasHigh = false;
                }
                if (!botWasHigh && gpio6) {
                    if ((currentTime = System.currentTimeMillis()) - timeStemp > 2000L) {
                        botWasHigh = true;
                        this.botLs = true;
                        timeStemp = currentTime;
                    }

                } else if (!gpio6) {
                    botWasHigh = false;
                }
                Thread.sleep(10L);
            }

        } catch (InterruptedException e) {
            e.printStackTrace();
            return;
        }
    }
}
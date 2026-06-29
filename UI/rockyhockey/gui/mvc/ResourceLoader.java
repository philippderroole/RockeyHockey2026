package rockyhockey.gui.mvc;

import java.io.InputStream;

public final class ResourceLoader {
    public static InputStream load(String path) {
        InputStream input = ResourceLoader.class.getResourceAsStream(path);
        if (input == null) {
            input = ResourceLoader.class.getResourceAsStream("/" + path);
        }
        return input;
    }
}
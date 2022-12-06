package libraryrat.dblp;

import java.net.URI;
import java.nio.file.Paths;

import io.vavr.control.Try;

import org.dblp.mmdb.RecordDbInterface;
import org.dblp.mmdb.RecordDb;

public class Loader {
    public static final Try<RecordDbInterface> createDb(String xmlFile, String dtdFile) {
        return Try.of(() -> {
            final URI xml = Loader.class.getResource(xmlFile).toURI();
            final URI dtd = Loader.class.getResource(dtdFile).toURI();
            return new RecordDb(Paths.get(xml).toString(), Paths.get(dtd).toString(), false);
        });
    }
}

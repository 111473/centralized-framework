package runners;

import org.testng.annotations.Test;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;

public class PythonScriptRunner {

    @Test
    public void printPythonScriptContents() {
        String filePath = "scripts/sum.py"; // Adjust if needed

        try (BufferedReader reader = new BufferedReader(new FileReader(filePath))) {
            String line;
            System.out.println("Contents of sum.py:");
            while ((line = reader.readLine()) != null) {
                System.out.println(line); // Prints each line of the script
            }
        } catch (IOException e) {
            System.err.println("Failed to read sum.py:");
            e.printStackTrace();
        }
    }
}

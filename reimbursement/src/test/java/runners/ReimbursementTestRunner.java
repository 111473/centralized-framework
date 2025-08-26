package runners;

import io.cucumber.testng.AbstractTestNGCucumberTests;
import io.cucumber.testng.CucumberOptions;
import org.testng.annotations.DataProvider;

@CucumberOptions(
        features = "src/test/resources/features",
        glue = {
                "com.testautomation.reimbursement.steps",
                "com.testautomation.framework.hooks"
        },
        tags = "@playwright", // Optional if you want to filter
        plugin = {
                "pretty",
                "html:target/playwright-cucumber-report.html",
                "io.qameta.allure.cucumber7jvm.AllureCucumber7Jvm"
        },
        monochrome = true
)
public class ReimbursementTestRunner extends AbstractTestNGCucumberTests {
        /**
         * Enables parallel execution of scenarios using TestNG's DataProvider.
         */
        @Override
        @DataProvider(parallel = true) // ✅ Enables parallel execution
        public Object[][] scenarios() {
                return super.scenarios();
        }
}

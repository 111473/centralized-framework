package runners;

import io.cucumber.testng.AbstractTestNGCucumberTests;
import io.cucumber.testng.CucumberOptions;
import org.testng.annotations.DataProvider;

@CucumberOptions(
        features = "src/test/resources/features",
        glue = {
                "com.testautomation.loanaccount.steps",
                "com.testautomation.framework.hooks"
        },
        tags = "@selenium",
        plugin = {
                "pretty",
                "html:target/selenium-cucumber-reports.html",
                "io.qameta.allure.cucumber7jvm.AllureCucumber7Jvm"
        },
        monochrome = true
)
public class LoanAccountTestRunner extends AbstractTestNGCucumberTests {

        /**
         * Enables parallel execution of scenarios using TestNG's DataProvider.
         */
        @Override
        @DataProvider(parallel = true) // ✅ enables thread-safe parallel scenarios
        public Object[][] scenarios() {
                return super.scenarios();
        }
}

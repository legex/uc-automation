import java.io.BufferedWriter;
import java.io.FileInputStream;
import java.io.FileWriter;
import java.io.InputStreamReader;
import java.io.BufferedReader;
import java.io.OutputStreamWriter;
import java.util.Base64;
import java.net.URL;
import java.security.cert.CertificateException;
import java.security.cert.X509Certificate;

import javax.net.ssl.HostnameVerifier;
import javax.net.ssl.HttpsURLConnection;
import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLSession;
import javax.net.ssl.SSLSocketFactory;
import javax.net.ssl.TrustManager;
import javax.net.ssl.X509TrustManager;

import org.apache.xerces.parsers.DOMParser;
import org.w3c.dom.Node;
import org.w3c.dom.traversal.DocumentTraversal;
import org.w3c.dom.traversal.NodeFilter;
import org.w3c.dom.traversal.TreeWalker;
import org.xml.sax.InputSource;

/**
 */
public class AxlSqlToolkit {

    /** DOCUMENT ME! */
    private String port = "8443";

    /** DOCUMENT ME! */
    private String host = "localhost";

    private String username = null;

    private String password = null;
    
    /**  */
    private String outputFile = "sample.response";
    private String inputFile = "sample.xml";
    
    private String currentStatement = null;

    private static String axlVersion = "14.0";

    /**
     * This method provides the ability to initialize the SOAP connection
     */
    private void init() {
        try {
            X509TrustManager xtm = new MyTrustManager();
            TrustManager[] mytm = { xtm };
            SSLContext ctx = SSLContext.getInstance("TLSv1.2");
            ctx.init(null, mytm, null);
            SSLSocketFactory sf = ctx.getSocketFactory();

            HttpsURLConnection.setDefaultSSLSocketFactory(sf);
            HttpsURLConnection.setDefaultHostnameVerifier(new HostnameVerifier() {
                public boolean verify(String hostname, SSLSession session) {
                    return true;
                }
            });
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     */
    public String createSqlMessage(String cmdName, String sql) {
        String soapMessage = "<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:ns=\"http://www.cisco.com/AXL/API/" +axlVersion+ "\">";
        soapMessage += "<soapenv:Header/><soapenv:Body><ns:"+cmdName+"><sql>"+sql+"</sql></ns:"+cmdName+"></soapenv:Body></soapenv:Envelope>";
        return soapMessage;
    }

    /**
     * DOCUMENT ME!
     * 
     * @return DOCUMENT ME!
     */
    public String getUrlEndpoint() {
        return "https://" + host + ":" + port + "/axl/";
    }

    /**
     * This method provides the ability to send a specific SOAPMessage
     * 
     * @param requestMessage The message to send
     */
    public void sendMessage(String requestMessage,String cmdName) throws Exception {
        try {
            String underLine = "---------------------";
            System.out.println("*****************************************************************************");
            System.out.println("Sending message : ");
            System.out.println(underLine);
            System.out.println(requestMessage);
            System.out.println();
            
            URL url = new URL(getUrlEndpoint());
            HttpsURLConnection conn = (HttpsURLConnection) url.openConnection();
            conn.setDoOutput(true);
            conn.setRequestProperty("SOAPAction","\"CUCM:DB ver=" +axlVersion+ " " +cmdName+"\"");
            conn.setRequestProperty("Content-Type","text/xml");
            String authorization = username+":"+password;
            conn.setRequestProperty("Authorization","Basic " + Base64.getEncoder().encodeToString(authorization.getBytes()));

            //Create an OutputStreamWriter for the URLConnection object and make the request
            try(OutputStreamWriter writer = new OutputStreamWriter(conn.getOutputStream());) {
                writer.write(requestMessage);
                writer.flush();

                //Read the response

                String line;
                try (BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream()));
                    FileWriter fw = new FileWriter(outputFile, true);
                    BufferedWriter bw = new BufferedWriter(fw);) {

                    bw.write("---------------------------- " + currentStatement + " ----------------------------");
                    bw.newLine();
                    System.out.println("Response : ");
                    System.out.println(underLine);

                    //Output the response to the console
                    while ((line = reader.readLine()) != null) {
                        System.out.println(line);
                        bw.write(line);
                        bw.newLine();
                    }
                    System.out.println();
                } catch (Exception ex) {
                    ex.printStackTrace();
                    try (BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getErrorStream()));
                        FileWriter fw = new FileWriter(outputFile, true);
                        BufferedWriter bw = new BufferedWriter(fw);) {
                        bw.write("---------------------------- " + currentStatement + " ----------------------------");
                        bw.newLine();
                        System.out.println(underLine);
                        while ((line = reader.readLine()) != null) {
                            System.out.println(line);
                            bw.write(line);
                            bw.newLine();
                        }
                    }
                }
            }

        }
        catch (Exception e) {
            e.printStackTrace();
            throw e;
        }
    }

    /**
     * This method provides the ability to execute the unit testing
     */
    private void execute() {
        try {
            // first, initialize the output file
            new FileWriter(outputFile).close();
            // now look through the source file for SQL statements
            DOMParser parser = new DOMParser();
            parser.parse(new InputSource(new FileInputStream(inputFile)));
            Node rootNode = parser.getDocument().getDocumentElement();
            TreeWalker propWalker = ((DocumentTraversal) parser.getDocument()).createTreeWalker(rootNode, NodeFilter.SHOW_ELEMENT, (NodeFilter) new GenericNodeFilter("sql"), true);
            Node currProp = propWalker.firstChild();
            while (currProp != null) {
                Node queryNode = currProp.getAttributes().getNamedItem("query");
                Node updateNode = currProp.getAttributes().getNamedItem("update");
                if (queryNode != null) {
                    // do the query
                    currentStatement = queryNode.getNodeValue();
                    System.out.println(currentStatement);
                    sendMessage(createSqlMessage("executeSQLQuery", currentStatement),"executeSQLQuery");
                }
                else if (updateNode != null){
                    currentStatement = updateNode.getNodeValue();
                    System.out.println(currentStatement);
                    sendMessage(createSqlMessage("executeSQLUpdate", currentStatement),"executeSQLUpdate");
                }
                else {
                    System.out.println("SQL element did not contain a query or update attribute");
                }
                currProp = propWalker.nextSibling();
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    public class GenericNodeFilter implements NodeFilter {
        String theNodeName = null;

        public GenericNodeFilter(String _nodeName) {
            theNodeName = _nodeName;
        }

        public short acceptNode(Node _node) {
            if (_node.getNodeName().equals(theNodeName)) {
                return NodeFilter.FILTER_ACCEPT;
            }
            else {
                return NodeFilter.FILTER_REJECT;
            }
        }
    }

    /**
     * This method provides the main method for the class
     * 
     * @param args Standard Java PSVM arguments
     */
    public static void main(String[] args) {
        try {
            AxlSqlToolkit ast = new AxlSqlToolkit();
            ast.parseArgs(args);
            ast.init();
            ast.execute();
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     * DOCUMENT ME!
     * 
     * @param args DOCUMENT ME!
     */
    private void parseArgs(String[] args) {
        if (args.length == 0) {
            usage();
            System.exit(-1);
        }
        for (int i = 0; i < args.length; i++) {
            if (args[i].startsWith("-username")) {
                username = args[i].substring(args[i].indexOf("=") + 1, args[i].length());
            }
            else if (args[i].startsWith("-password")) {
                password = args[i].substring(args[i].indexOf("=") + 1, args[i].length());
            }
            else if (args[i].startsWith("-host")) {
                host = args[i].substring(args[i].indexOf("=") + 1, args[i].length());
            }
            else if (args[i].startsWith("-port")) {
                port = args[i].substring(args[i].indexOf("=") + 1, args[i].length());
            }
            else if (args[i].startsWith("-input")) {
                inputFile = args[i].substring(args[i].indexOf("=") + 1, args[i].length());
            }
            else if (args[i].startsWith("-output")) {
                outputFile = args[i].substring(args[i].indexOf("=") + 1, args[i].length());
            }
            else {
                usage();
                System.exit(-1);
            }
        }
    }

    /**
     * DOCUMENT ME!
     */
    private void usage() {
        System.out.println("AxlTestDriver (Java) parameters and options:");
        System.out.println("  -username=<value>: use the specified username instead of default");
        System.out.println("  -password=<value>: use the specified password instead of default");
        System.out.println("  -host=<hostname or IP>: use the specified hostname");
        System.out.println("  -port=<portnumber>: use the specified portnumber");
        System.out.println("  -input=<filename>: use the specified file as the source of the sql statements");
        System.out.println("  -output=<filename>: use the specified file as the destination of the AXL responses");
    }

    /* testing the SSL interface */
    public class MyTrustManager implements X509TrustManager {
        MyTrustManager() {}
        public void checkClientTrusted(X509Certificate chain[], String authType) throws CertificateException {}
        public void checkServerTrusted(X509Certificate chain[], String authType) throws CertificateException {}
        public X509Certificate[] getAcceptedIssuers() {
            return null;
        }
    }
}

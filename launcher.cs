using System;
using System.Diagnostics;
using System.IO;

namespace JarvisLauncher
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.Title = "J.A.R.V.I.S. Desktop & Voice Agent";
            Console.ForegroundColor = ConsoleColor.Cyan;
            Console.WriteLine("==================================================");
            Console.WriteLine("   J.A.R.V.I.S. Desktop & Voice Assistant         ");
            Console.WriteLine("==================================================");
            Console.ResetColor();

            string jarvisDir = @"d:\Jarvis";
            string pythonScript = Path.Combine(jarvisDir, "main.py");

            if (!Directory.Exists(jarvisDir))
            {
                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine("Error: Directory D:\\Jarvis does not exist!");
                Console.ResetColor();
                Console.WriteLine("Press any key to exit...");
                Console.ReadKey();
                return;
            }

            ProcessStartInfo psi = new ProcessStartInfo();
            psi.FileName = "python.exe";
            psi.WorkingDirectory = jarvisDir;

            // Forward arguments if any were provided
            if (args != null && args.Length > 0)
            {
                psi.Arguments = "main.py " + string.Join(" ", args);
            }
            else
            {
                psi.Arguments = "main.py";
            }

            psi.UseShellExecute = false;

            try
            {
                Process proc = Process.Start(psi);
                if (proc != null)
                {
                    proc.WaitForExit();
                }
            }
            catch (Exception ex)
            {
                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine("Failed to launch Jarvis: " + ex.Message);
                Console.ResetColor();
                Console.WriteLine("Press any key to exit...");
                Console.ReadKey();
            }
        }
    }
}

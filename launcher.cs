using System;
using System.Diagnostics;
using System.IO;

namespace JarvisLauncher
{
    class Program
    {
        [STAThread]
        static void Main(string[] args)
        {
            string jarvisDir = @"d:\Jarvis";
            string pythonwPath = @"C:\Python314\pythonw.exe";
            if (!File.Exists(pythonwPath))
            {
                pythonwPath = "pythonw.exe";
            }

            ProcessStartInfo psi = new ProcessStartInfo();
            psi.FileName = pythonwPath;
            psi.Arguments = "gui.py";
            psi.WorkingDirectory = jarvisDir;
            psi.UseShellExecute = false;
            psi.CreateNoWindow = true;

            try
            {
                Process.Start(psi);
            }
            catch (Exception ex)
            {
                // Fallback attempt with python.exe if pythonw fails
                try
                {
                    psi.FileName = "python.exe";
                    Process.Start(psi);
                }
                catch
                {
                    // ignore
                }
            }
        }
    }
}

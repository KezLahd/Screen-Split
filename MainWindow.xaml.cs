using System;
using System.Collections.Generic;
using System.Windows;
using System.Windows.Forms;
using System.Windows.Media.Imaging;
using System.Drawing;
using System.Windows.Interop;
using System.Runtime.InteropServices;
using System.Windows.Threading;
using AForge.Video;
using AForge.Video.DirectShow;
using System.Windows.Media;

namespace ScreenSplitApp
{
    public partial class MainWindow : Window
    {
        private Dictionary<string, IntPtr> windowHandles = new Dictionary<string, IntPtr>();
        private VideoCaptureDevice videoSource;
        private DispatcherTimer windowCaptureTimer;
        private bool isCameraEnabled = false;
        private bool isWindowCaptureEnabled = false;

        [DllImport("user32.dll")]
        private static extern bool EnumWindows(EnumWindowsProc enumProc, IntPtr lParam);

        [DllImport("user32.dll")]
        private static extern bool IsWindowVisible(IntPtr hWnd);

        [DllImport("user32.dll")]
        private static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder lpString, int nMaxCount);

        [DllImport("user32.dll")]
        private static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);

        [StructLayout(LayoutKind.Sequential)]
        private struct RECT
        {
            public int Left;
            public int Top;
            public int Right;
            public int Bottom;
        }

        private delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

        public MainWindow()
        {
            InitializeComponent();
            RefreshWindowList();
        }

        private void RefreshWindowList()
        {
            WindowComboBox.Items.Clear();
            WindowComboBox.Items.Add("Select a window...");
            windowHandles.Clear();

            EnumWindows((hWnd, lParam) =>
            {
                if (IsWindowVisible(hWnd))
                {
                    var sb = new System.Text.StringBuilder(256);
                    if (GetWindowText(hWnd, sb, 256) > 0)
                    {
                        string title = sb.ToString();
                        if (!string.IsNullOrEmpty(title) && title != this.Title)
                        {
                            windowHandles[title] = hWnd;
                            WindowComboBox.Items.Add(title);
                        }
                    }
                }
                return true;
            }, IntPtr.Zero);

            WindowComboBox.SelectedIndex = 0;
        }

        private void RefreshButton_Click(object sender, RoutedEventArgs e)
        {
            RefreshWindowList();
        }

        private void WindowComboBox_SelectionChanged(object sender, System.Windows.Controls.SelectionChangedEventArgs e)
        {
            if (WindowComboBox.SelectedIndex <= 0)
            {
                StopWindowCapture();
                WindowStatus.Text = "Select a window from the dropdown";
                return;
            }

            string selectedTitle = WindowComboBox.SelectedItem.ToString();
            if (windowHandles.TryGetValue(selectedTitle, out IntPtr hwnd))
            {
                StartWindowCapture(hwnd);
            }
        }

        private void StartWindowCapture(IntPtr hwnd)
        {
            StopWindowCapture();

            windowCaptureTimer = new DispatcherTimer();
            windowCaptureTimer.Interval = TimeSpan.FromMilliseconds(100); // 10 FPS
            windowCaptureTimer.Tick += (s, e) => CaptureWindow(hwnd);
            windowCaptureTimer.Start();
            isWindowCaptureEnabled = true;
        }

        private void StopWindowCapture()
        {
            if (windowCaptureTimer != null)
            {
                windowCaptureTimer.Stop();
                windowCaptureTimer = null;
            }
            isWindowCaptureEnabled = false;
        }

        private void CaptureWindow(IntPtr hwnd)
        {
            try
            {
                if (!IsWindowVisible(hwnd))
                {
                    WindowStatus.Text = "Window no longer exists";
                    StopWindowCapture();
                    return;
                }

                RECT rect;
                if (GetWindowRect(hwnd, out rect))
                {
                    int width = rect.Right - rect.Left;
                    int height = rect.Bottom - rect.Top;

                    if (width > 0 && height > 0)
                    {
                        using (Bitmap bitmap = new Bitmap(width, height))
                        {
                            using (Graphics graphics = Graphics.FromImage(bitmap))
                            {
                                graphics.CopyFromScreen(rect.Left, rect.Top, 0, 0, new System.Drawing.Size(width, height));
                            }

                            WindowDisplay.Source = Imaging.CreateBitmapSourceFromHBitmap(
                                bitmap.GetHbitmap(),
                                IntPtr.Zero,
                                Int32Rect.Empty,
                                BitmapSizeOptions.FromEmptyOptions());
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                WindowStatus.Text = "Error capturing window";
                System.Diagnostics.Debug.WriteLine($"Window capture error: {ex.Message}");
            }
        }

        private void CameraButton_Click(object sender, RoutedEventArgs e)
        {
            if (!isCameraEnabled)
            {
                StartCamera();
            }
            else
            {
                StopCamera();
            }
        }

        private void StartCamera()
        {
            try
            {
                var videoDevices = new FilterInfoCollection(FilterCategory.VideoInputDevice);
                if (videoDevices.Count == 0)
                {
                    MessageBox.Show("No video devices found", "Camera Error", MessageBoxButton.OK, MessageBoxImage.Error);
                    return;
                }

                videoSource = new VideoCaptureDevice(videoDevices[0].MonikerString);
                videoSource.NewFrame += VideoSource_NewFrame;
                videoSource.Start();
                isCameraEnabled = true;
                CameraButton.Content = "Disable Camera";
                CameraStatus.Text = "Initializing camera...";
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error starting camera: {ex.Message}", "Camera Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void StopCamera()
        {
            if (videoSource != null && videoSource.IsRunning)
            {
                videoSource.SignalToStop();
                videoSource.WaitForStop();
                videoSource = null;
            }
            isCameraEnabled = false;
            CameraButton.Content = "Enable Camera";
            CameraStatus.Text = "Camera disabled";
        }

        private void VideoSource_NewFrame(object sender, NewFrameEventArgs eventArgs)
        {
            try
            {
                using (Bitmap bitmap = (Bitmap)eventArgs.Frame.Clone())
                {
                    CameraDisplay.Dispatcher.Invoke(() =>
                    {
                        CameraDisplay.Source = Imaging.CreateBitmapSourceFromHBitmap(
                            bitmap.GetHbitmap(),
                            IntPtr.Zero,
                            Int32Rect.Empty,
                            BitmapSizeOptions.FromEmptyOptions());
                        CameraStatus.Text = "Camera active";
                    });
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Camera error: {ex.Message}");
            }
        }

        protected override void OnClosing(System.ComponentModel.CancelEventArgs e)
        {
            StopCamera();
            StopWindowCapture();
            base.OnClosing(e);
        }
    }
} 
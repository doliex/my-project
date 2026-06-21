using System;
using System.Diagnostics;
using System.Threading;
using System.Threading.Tasks;

public class Program
{
    public static void Main()
    {
        // Giới hạn 1 tỷ số
        long limit = 1_000_000_000; 
        
        Console.WriteLine($"Khởi động tới mốc {limit:N0}...");
        Console.WriteLine("Cấu hình: Sử dụng 6/8 nhân (Đã thiết lập ParallelOptions).");
        
        Stopwatch sw = Stopwatch.StartNew();
        long counter = 0;

        // Thiết lập giới hạn 6 nhân
        ParallelOptions options = new ParallelOptions 
        { 
            MaxDegreeOfParallelism = 6 
        };

        // Chạy đa luồng
        Parallel.For(1, limit / 2, options, i =>
        {
            long n = 2 * i + 1; // Chỉ xét số lẻ
            long current = n;

            // Vòng lặp tối ưu
            while (current >= n)
            {
                if (current % 2 == 0)
                {
                    current >>= 1; 
                }
                else
                {
                    current = (3 * current + 1) >> 1;
                }
            }
            
            Interlocked.Increment(ref counter);
            
            // Báo cáo mỗi 50 triệu số lẻ (tương đương 100 triệu số thực tế)
            if (counter % 50_000_000 == 0)
            {
                Console.WriteLine($"Tiến độ: {counter * 2:N0} | Thời gian: {sw.Elapsed.TotalSeconds:F2} giây");
            }
        });

        sw.Stop();
        
        Console.WriteLine("--------------------------------------------------");
        Console.WriteLine($"HOÀN TẤT!");
        Console.WriteLine($"Tổng thời gian: {sw.Elapsed.TotalSeconds:F4} giây");
        Console.WriteLine("--------------------------------------------------");
    }
}

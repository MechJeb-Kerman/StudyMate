"""buggy.py · 被对拍的那一版候选解（给好的，**别改、别删**）

这是别人交上来的「二分查找」：在升序数组 a 里找 x，找到交回它的下标，没有交回 -1。
它跑起来一行报错都没有，样例上也能过——但它藏着第 14 课那三种错法里的第一种：

    区间用的是闭区间 [lo, hi]，循环条件却写成 while lo < hi，于是「区间只剩一格」
    那一步直接跳出了循环；循环结束之后又直接 return -1，那一格从来没被检查过。

这一课不对着题面讨论它对不对，只把它当**候选解**扔给你的对拍器：
参照解（你自己写的 brute_find）说 1、它说 -1 的时候，反例就抓到了。

别改这个文件：判分拿它当「一定要抓到的东西」，改了它（比如顺手把 bug 修了）
第 3 层就没东西可抓了。`tools.load_buggy()` 会按行读它，好把出错的行号打印出来。

接口：函数名 cand_find、参数顺序 (a, x) 都是判分接口，别改。
"""


def cand_find(a, x):
    """在升序数组 a 里找 x：找到交回下标，没有交回 -1。（这一版有 bug，别改）"""
    lo = 0
    hi = len(a) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] == x:
            return mid
        if a[mid] < x:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


if __name__ == '__main__':                     # 别改：这层守卫让判分 import 它时不出声
    for arr, target in [([], 3), ([5], 5), ([63, 97], 97), ([1, 3, 5, 7], 1)]:
        print('buggy 自查 a=' + repr(arr) + ' x=' + repr(target)
              + ' → ' + repr(cand_find(arr, target)))

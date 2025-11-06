/sc:brainstorm  ```
1. 我要重新設計整個畫面，請看這張圖：refData/design/new_design.png
2. 畫面分成三個部份。
3. 最左邊是輸入文字、投影片張數、模板樣式和佈景主題。
4. generate presentation method of presenton APIs contains template(模版樣式) 及 theme(佈景主題)
5. 在圖中最右邊部份，在內容輸入框下面是投影片數量及下拉式選單。這邊要改成一個「-」按鈕、一個「+」按鈕、一個文字框。
6. 按「+」按鈕，則文字框內的數字往上加，按「-」按鈕，則文字框內的數字往下減，直到0
6. 在「投影片張數」下方是「模版樣式」，是一個下拉式選單。
7. 在模版樣式的下拉式選單的下方是「佈景主題」，下面是主題的下拉式選單。
7. presenton提供四種templates:general, modern, standard, swift。
8. presenton提供5種themes:edge-yellow, mint-blue, light-rose, professional-blue, professional-dark。
9. template 及 theme 對應generate參數中的template及theme。
10. 最下面是「生成簡報」及「清除」二個按鈕。
11. 整個畫面的中間部份是產生完成的投影片及演講稿產生的部份。
12. 產生完成投影片縮圖會排列成一列，可以左右捲動看到不同的投影片。
13. 而當使者點擊一張投影片時，這張投影片會在最右邊那裏的上半部呈現出來。
14. 在這個「投影片列」下方，維持三個按鈕，分別是[下載PPT]、[下載PDF]、[生成演講稿]。
15. 在三個按鈕下方是「演講稿」文字，右邊是[下載演講稿]按鈕及選擇演講稿類型的下拉式選單。
16. 當演講稿完成後，當點擊一張投影片時，這張投影片會在最右邊那裏的上半部呈現出來。下半部則是這張投影片的演講稿。

``` 

general
modern
standard
swift

edge-yellow
mint-blue  薄荷藍
light-rose  淺玫瑰紅
professional-blue  專業藍
professional-dark  專業黑
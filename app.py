import streamlit as st
from PIL import Image
import io
import zipfile

st.set_page_config(page_title="PNG限界圧縮ツール", layout="centered")

st.title("🖼️ PNG限界ギリギリ圧縮ツール")
st.write("複数のPNG画像をまとめてアップロードし、それぞれ指定サイズを超えない限界の最高画質へ自動計算します。")

# 設定エリア
uploaded_files = st.file_uploader("PNG画像をアップロードしてください（複数可）", type=["png"], accept_multiple_files=True)
target_mb = st.number_input("目標の上限サイズ (MB)", min_value=0.1, max_value=50.0, value=5.0, step=0.1)

if uploaded_files:
    absolute_max_bytes = int(target_mb * 1000 * 1000)
    target_bytes = int(absolute_max_bytes * 0.98)
    
    # 選択されたファイル数と設定を事前に確認
    st.info(f"📁 {len(uploaded_files)} 枚の画像が選択されています。目標上限：{target_mb} MB ({absolute_max_bytes:,} バイト)")
    
    # ─── ここに「スタートボタン」を配置 ───
    # ボタンが押されたら st.button("...") が True になります
    if st.button("🚀 圧縮スタート", type="primary", use_container_width=True):
        
        # 圧縮後のデータを溜めておく辞書
        compressed_images = {}
        
        st.write(f"### 📦 各画像の処理結果")
        
        # アップロードされた画像をループ処理
        for uploaded_file in uploaded_files:
            with st.expander(f"📄 {uploaded_file.name}", expanded=True):
                img = Image.open(uploaded_file)
                orig_bytes = uploaded_file.size
                
                st.write(f"元のサイズ: {orig_bytes:,} バイト ({orig_bytes / 1000 / 1000:.2f} MB)")
                
                if orig_bytes <= absolute_max_bytes:
                    st.success("元の画像はすでに目標サイズ以下です！圧縮せずに保持します。")
                    compressed_images[uploaded_file.name] = uploaded_file.getvalue()
                else:
                    # 二分探索で高速圧縮
                    low = 0.01
                    high = 0.99
                    best_data = None
                    closest_size = 0
                    
                    # 最初はリサイズなしの最適化を試す
                    buf = io.BytesIO()
                    img.save(buf, format="PNG", optimize=True)
                    current_size = buf.tell()
                    
                    if current_size <= target_bytes:
                        best_data = buf.getvalue()
                        closest_size = current_size
                    else:
                        # ダメなら二分探索
                        for _ in range(10):
                            mid = (low + high) / 2
                            w, h = int(img.width * mid), int(img.height * mid)
                            
                            if w < 1 or h < 1:
                                high = mid
                                continue
                                
                            buf = io.BytesIO()
                            resized_img = img.resize((w, h), Image.Resampling.LANCZOS)
                            resized_img.save(buf, format="PNG", optimize=True)
                            current_size = buf.tell()
                            
                            if current_size <= target_bytes:
                                closest_size = current_size
                                best_data = buf.getvalue()
                                low = mid
                            else:
                                high = mid
                    
                    if best_data:
                        st.success(f"限界まで圧縮成功: {closest_size:,} バイト")
                        compressed_images[uploaded_file.name] = best_data
                    else:
                        st.error("圧縮に失敗しました。")

        # --- 一括ダウンロードエリア ---
        st.write("---")
        st.write("### 📥 ダウンロード")
        
        if len(compressed_images) == 1:
            file_name = list(compressed_images.keys())[0]
            st.download_button(
                label="圧縮したPNGをダウンロード",
                data=compressed_images[file_name],
                file_name=f"compressed_{file_name}",
                mime="image/png",
                use_container_width=True
            )
        elif len(compressed_images) > 1:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for file_name, data in compressed_images.items():
                    zip_file.writestr(f"compressed_{file_name}", data)
                    
            st.download_button(
                label=f"🎬 圧縮した全画像 ({len(compressed_images)}枚) をZIPで一括ダウンロード",
                data=zip_buffer.getvalue(),
                file_name="compressed_images.zip",
                mime="application/zip",
                use_container_width=True
            )
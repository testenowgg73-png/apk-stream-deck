package com.ultron.streamdeck;

import android.app.Activity;
import android.app.AlertDialog;
import android.os.Bundle;
import android.os.AsyncTask;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.BitmapFactory;
import android.graphics.Bitmap;
import android.graphics.Movie;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;
import android.graphics.drawable.Drawable;
import android.net.Uri;
import android.os.SystemClock;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.View;
import android.view.inputmethod.InputMethodManager;
import android.content.Context;
import android.content.Intent;
import android.widget.*;
import org.json.JSONObject;
import java.io.*;
import java.net.Socket;
import java.util.HashMap;
import java.util.Map;

public class MainActivity extends Activity {
    private EditText hostEdit, portEdit, tokenEdit;
    private TextView status;
    private SharedPreferences prefs;
    private final Map<String, FrameLayout> buttonCells = new HashMap<String, FrameLayout>();
    private final Map<String, ImageView> buttonImages = new HashMap<String, ImageView>();
    private final Map<String, GifView> buttonGifs = new HashMap<String, GifView>();
    private String pickingButtonId;
    private static final int PICK_IMAGE = 701;
    private final int RED=Color.rgb(255,48,56), BG=Color.rgb(9,9,13), PANEL=Color.rgb(25,25,33), MUTED=Color.rgb(165,165,178);

    @Override public void onCreate(Bundle b) {
        super.onCreate(b); getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
        prefs=getSharedPreferences("ultron",MODE_PRIVATE);
        LinearLayout root=new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setPadding(12,8,12,8); root.setBackgroundColor(BG);
        TextView title=new TextView(this); title.setText("ULTRON  //  STREAM DECK"); title.setTextColor(RED); title.setTextSize(24); title.setTypeface(Typeface.DEFAULT,Typeface.BOLD); title.setGravity(Gravity.CENTER); root.addView(title,new LinearLayout.LayoutParams(-1,-2));
        TextView sub=new TextView(this); sub.setText("PC CONTROL SYSTEM  •  USB TETHERING"); sub.setTextColor(MUTED); sub.setTextSize(10); sub.setGravity(Gravity.CENTER); root.addView(sub);
        LinearLayout conn=new LinearLayout(this); conn.setOrientation(LinearLayout.HORIZONTAL); conn.setGravity(Gravity.CENTER_VERTICAL); conn.setPadding(0,8,0,8);
        hostEdit=field(prefs.getString("host","192.168.42.129"),"IP do PC"); portEdit=field(prefs.getString("port","8765"),"Porta"); tokenEdit=field(prefs.getString("token","ULTRON-CHANGE-ME-7429"),"Token");
        conn.addView(hostEdit,new LinearLayout.LayoutParams(0,44,2)); conn.addView(portEdit,new LinearLayout.LayoutParams(0,44,1)); conn.addView(tokenEdit,new LinearLayout.LayoutParams(0,44,2));
        Button save=button("CONECTAR / SALVAR",RED); save.setOnClickListener(v->{prefs.edit().putString("host",hostEdit.getText().toString().trim()).putString("port",portEdit.getText().toString().trim()).putString("token",tokenEdit.getText().toString().trim()).apply(); hideKeyboard(); setStatus("Configuração salva. Toque em um botão para testar.");}); conn.addView(save,new LinearLayout.LayoutParams(0,44,1)); root.addView(conn);
        ScrollView scroll=new ScrollView(this); LinearLayout grid=new LinearLayout(this); grid.setOrientation(LinearLayout.VERTICAL); scroll.addView(grid);
        addRow(grid, new String[][]{{"♫\nPLAY / PAUSE","music_play"},{"⏭\nPRÓXIMA","music_next"},{"⏮\nANTERIOR","music_prev"},{"＋\nVOLUME +","vol_up"}});
        addRow(grid, new String[][]{{"－\nVOLUME -","vol_down"},{"◖\nMUDO","vol_mute"},{"CTRL + C\nCOPIAR","shortcut_copy"},{"CTRL + V\nCOLAR","shortcut_paste"}});
        addRow(grid, new String[][]{{"ALT + TAB\nJANELAS","shortcut_alt_tab"},{"WIN + D\nDESKTOP","shortcut_desktop"},{"SPOTIFY\nABRIR","open_spotify"},{"NAVEGADOR\nABRIR","open_browser"}});
        addRow(grid, new String[][]{{"SCRIPT 01\nEXECUTAR","script_1"},{"SCRIPT 02\nEXECUTAR","script_2"},{"F1\nTECLA DE JOGO","game_key"},{"F5\nATUALIZAR","shortcut_f5"}});
        root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1)); status=new TextView(this); status.setText("Pronto. No PC, abra o ULTRON e inicie o servidor."); status.setTextColor(MUTED); status.setTextSize(12); status.setGravity(Gravity.CENTER); status.setPadding(2,6,2,2); root.addView(status,new LinearLayout.LayoutParams(-1,-2)); setContentView(root);
    }
    private EditText field(String value,String hint){ EditText e=new EditText(this); e.setSingleLine(true); e.setText(value); e.setHint(hint); e.setHintTextColor(MUTED); e.setTextColor(Color.WHITE); e.setTextSize(11); e.setPadding(7,0,7,0); e.setBackground(shape(PANEL,1,Color.rgb(65,65,78))); return e; }
    private GradientDrawable shape(int color,int stroke,int strokeColor){ GradientDrawable d=new GradientDrawable(); d.setColor(color); d.setCornerRadius(8); d.setStroke(stroke,strokeColor); return d; }
    private Button button(String text,int color){ Button b=new Button(this); b.setText(text); b.setTextColor(Color.WHITE); b.setTextSize(11); b.setAllCaps(false); b.setPadding(2,2,2,2); b.setBackground(shape(color,1,Color.rgb(255,100,100))); return b; }
    private void addRow(LinearLayout parent,String[][] items){
        LinearLayout row=new LinearLayout(this); row.setOrientation(LinearLayout.HORIZONTAL);
        for(String[] item:items){
            final String id=item[1]; final String label=item[0];
            FrameLayout cell=new FrameLayout(this); cell.setBackground(shape(PANEL,2,RED));
            Button b=button("",PANEL); b.setText(""); b.setOnClickListener(v->sendAction(id));
            b.setOnLongClickListener(v->{ chooseButtonImage(id); return true; });
            cell.addView(b,new FrameLayout.LayoutParams(-1,-1));
            TextView caption=new TextView(this); caption.setText(label); caption.setTextColor(Color.WHITE); caption.setTextSize(10); caption.setGravity(Gravity.CENTER); caption.setBackgroundColor(Color.argb(210,9,9,13)); caption.setPadding(2,4,2,4);
            FrameLayout.LayoutParams cp=new FrameLayout.LayoutParams(-1,-2,Gravity.BOTTOM); cell.addView(caption,cp); caption.setOnClickListener(v->sendAction(id)); caption.setOnLongClickListener(v->{chooseButtonImage(id);return true;});
            LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(0,0,1); lp.height=(int)(getResources().getDisplayMetrics().heightPixels*0.14); lp.setMargins(4,4,4,4); row.addView(cell,lp);
            buttonCells.put(id,cell); loadButtonImage(id,cell,caption);
        } parent.addView(row);
    }
    private void chooseButtonImage(final String id){
        final String[] choices={"Escolher imagem / GIF","Remover imagem do botão"};
        new AlertDialog.Builder(this).setTitle("Personalizar botão").setItems(choices,(dialog,which)->{
            if(which==0){ pickingButtonId=id; Intent intent=new Intent(Intent.ACTION_GET_CONTENT); intent.setType("image/*"); intent.addCategory(Intent.CATEGORY_OPENABLE);
                try { startActivityForResult(Intent.createChooser(intent,"Escolha imagem ou GIF"),PICK_IMAGE); }
                catch(Exception e){setStatus("Não foi possível abrir a galeria: "+e.getMessage());}
            }else{ prefs.edit().remove("img_"+id).remove("gif_"+id).apply(); FrameLayout cell=buttonCells.get(id); if(cell!=null){ for(int i=cell.getChildCount()-1;i>=0;i--){View v=cell.getChildAt(i); if(v instanceof ImageView || v instanceof GifView)cell.removeViewAt(i);} } setStatus("Imagem removida do botão "+id); }
        }).show();
    }
    @Override protected void onActivityResult(int requestCode,int resultCode,Intent data){
        super.onActivityResult(requestCode,resultCode,data);
        if(requestCode!=PICK_IMAGE || resultCode!=RESULT_OK || data==null || data.getData()==null || pickingButtonId==null)return;
        final String id=pickingButtonId; final Uri uri=data.getData();
        try {
            InputStream in=getContentResolver().openInputStream(uri); if(in==null)throw new IOException("Arquivo indisponível");
            File dir=new File(getFilesDir(),"button_media"); if(!dir.exists())dir.mkdirs();
            String ext=".img"; String path=uri.getPath(); if(path!=null && path.toLowerCase().endsWith(".gif"))ext=".gif";
            // Detect GIF from its file signature, even when the content URI has no filename.
            File out=new File(dir,id+".media"); FileOutputStream fos=new FileOutputStream(out); byte[] buf=new byte[8192]; int n; ByteArrayOutputStream head=new ByteArrayOutputStream();
            while((n=in.read(buf))>0){fos.write(buf,0,n); if(head.size()<6)head.write(buf,0,Math.min(n,6-head.size()));} in.close(); fos.close();
            byte[] sig=head.toByteArray(); boolean gif=sig.length>=3 && sig[0]=='G' && sig[1]=='I' && sig[2]=='F';
            prefs.edit().putString("img_"+id,out.getAbsolutePath()).putBoolean("gif_"+id,gif).apply();
            FrameLayout cell=buttonCells.get(id); if(cell!=null){ TextView caption=null; for(int i=0;i<cell.getChildCount();i++) if(cell.getChildAt(i) instanceof TextView)caption=(TextView)cell.getChildAt(i); loadButtonImage(id,cell,caption); }
            setStatus(gif?"GIF aplicado ao botão "+id:"Imagem aplicada ao botão "+id);
        }catch(Exception e){setStatus("Erro ao importar imagem: "+e.getMessage());}
    }
    private void loadButtonImage(String id,FrameLayout cell,TextView caption){
        String old=prefs.getString("img_"+id,""); if(old.length()==0)return; File f=new File(old); if(!f.exists())return;
        // Remove previous media overlays, leaving the button and caption intact.
        for(int i=cell.getChildCount()-1;i>=0;i--){View v=cell.getChildAt(i); if(v instanceof ImageView || v instanceof GifView)cell.removeViewAt(i);}
        View media;
        if(prefs.getBoolean("gif_"+id,false)){ media=new GifView(this,f.getAbsolutePath()); }
        else { ImageView iv=new ImageView(this); Bitmap bm=BitmapFactory.decodeFile(f.getAbsolutePath()); if(bm==null)return; iv.setImageBitmap(bm); iv.setScaleType(ImageView.ScaleType.FIT_CENTER); media=iv; }
        media.setClickable(false); media.setFocusable(false); FrameLayout.LayoutParams mp=new FrameLayout.LayoutParams(-1,-1); mp.setMargins(7,5,7,25); cell.addView(media,mp);
    }
    private class GifView extends View {
        private Movie movie; private long started; private Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG|Paint.FILTER_BITMAP_FLAG);
        GifView(Context c,String path){super(c); try{FileInputStream in=new FileInputStream(path); byte[] bytes=new byte[in.available()]; int total=0,n; while(total<bytes.length && (n=in.read(bytes,total,bytes.length-total))>0)total+=n; in.close(); movie=Movie.decodeByteArray(bytes,0,total);}catch(Exception e){movie=null;} started=SystemClock.uptimeMillis(); setLayerType(View.LAYER_TYPE_SOFTWARE,null); }
        @Override protected void onDraw(Canvas canvas){super.onDraw(canvas); if(movie==null)return; int dur=movie.duration(); if(dur<=0)dur=1000; movie.setTime((int)((SystemClock.uptimeMillis()-started)%dur)); float scale=Math.min((float)getWidth()/Math.max(1,movie.width()),(float)getHeight()/Math.max(1,movie.height())); canvas.save(); canvas.translate((getWidth()-movie.width()*scale)/2f,(getHeight()-movie.height()*scale)/2f); canvas.scale(scale,scale); movie.draw(canvas,0,0,paint); canvas.restore(); invalidate(); }
    }

    private void hideKeyboard(){ try{ ((InputMethodManager)getSystemService(Context.INPUT_METHOD_SERVICE)).hideSoftInputFromWindow(tokenEdit.getWindowToken(),0); }catch(Exception e){} }
    private void setStatus(final String s){ runOnUiThread(()->status.setText(s)); }
    private void sendAction(String id){ String host=hostEdit.getText().toString().trim(), token=tokenEdit.getText().toString().trim(); int port; try{port=Integer.parseInt(portEdit.getText().toString().trim());}catch(Exception e){setStatus("Porta inválida.");return;} if(host.length()==0||token.length()==0){setStatus("Preencha IP e token.");return;} prefs.edit().putString("host",host).putString("port",String.valueOf(port)).putString("token",token).apply(); new SendTask(host,port,token,id).execute(); }
    private class SendTask extends AsyncTask<Void,Void,String>{ String host,token,id; int port; SendTask(String h,int p,String t,String a){host=h;port=p;token=t;id=a;} protected String doInBackground(Void... v){ Socket s=null; try{ s=new Socket(); s.connect(new java.net.InetSocketAddress(host,port),2500); s.setSoTimeout(2500); JSONObject o=new JSONObject(); o.put("token",token); o.put("action",id); BufferedWriter w=new BufferedWriter(new OutputStreamWriter(s.getOutputStream(),"UTF-8")); w.write(o.toString()+"\n"); w.flush(); BufferedReader r=new BufferedReader(new InputStreamReader(s.getInputStream(),"UTF-8")); String line=r.readLine(); return line==null?"PC conectado, sem resposta.":new JSONObject(line).optString("message",line); }catch(Exception e){return "Falha: "+e.getMessage()+". Confira IP, token e firewall.";}finally{try{if(s!=null)s.close();}catch(Exception e){}}} protected void onPostExecute(String s){setStatus(s);} }
}
